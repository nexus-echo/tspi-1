"""Documents + labs. Upload (patient own / staff) -> background OCR -> candidate labs ->
STAFF confirm/edit -> confirmed labs (the gate before plan generation in Phase D).
Raw files never leave MiHealth; only confirmed, de-identified labs are sent to TSPI later."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import audit, ocr, storage, tspi
from app.database import SessionLocal, get_db
from app.deps import get_current_user
from app.models import Document, LabResult, Patient, Role, User
from app.routers.patients import _authorize, _is_staff, _load_patient
from app.schemas import ConfirmLabsRequest, DocumentOut, LabResultIn, LabResultOut

router = APIRouter(tags=["documents"])


def run_ocr(document_id: str) -> None:
    """Background task: read the report and parse candidate labs, then set status. Own DB session.

    Primary path: the TSPI engine's LOCAL vision/text models (POST /extract) — much smarter than
    OCR at reading scanned reports and sonography images. Falls back to the local OCR/heuristic
    parser when the engine is unreachable. Candidates are always confirmed=False (human gate)."""
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if not doc:
            return
        rows: list[dict] = []
        note = ""
        source = "engine"
        got_content = False
        try:
            with open(doc.file_path, "rb") as fh:
                data = fh.read()
            result = tspi.extract_document(data, doc.original_filename, doc.mime_type, doc.doc_type)
            rows = result.get("labs", []) or []
            note = f"engine:{result.get('engine')} ({result.get('source')})"
            # capture any imaging narrative for the reviewer (kept out of the labs table)
            bits = []
            if result.get("imaging_modality"):
                bits.append(f"Modality: {result['imaging_modality']}")
            if result.get("imaging_impression"):
                bits.append(f"Impression: {result['imaging_impression']}")
            for f in (result.get("imaging_findings") or []):
                bits.append(f"- {f}")
            if result.get("narrative"):
                bits.append(str(result["narrative"]))
            if bits:
                note = note + " | " + " ".join(bits)
            if result.get("notes"):
                note = note + " | " + result["notes"]
            got_content = bool(rows) or bool(bits)
        except tspi.BrainUnavailable as e:
            # fall back to local OCR / heuristic parsing
            source = "ocr"
            text, onote = ocr.extract_text(doc.file_path, doc.mime_type, doc.original_filename)
            parsed = ocr.parse_labs(text)
            rows = [
                {"analyte": r["analyte"], "value": r.get("value"), "unit": r.get("unit"),
                 "ref_low": r.get("ref_low"), "ref_high": r.get("ref_high"), "flag": None}
                for r in parsed
            ]
            note = f"local-ocr:{onote} (engine offline: {type(e).__name__})"
            got_content = bool(text.strip())

        for r in rows:
            db.add(LabResult(
                patient_id=doc.patient_id, document_id=doc.id,
                analyte=r["analyte"], value=str(r.get("value", "")), unit=r.get("unit"),
                ref_low=r.get("ref_low"), ref_high=r.get("ref_high"),
                flag=r.get("flag"), source=source, confirmed=False,
            ))
        doc.ocr_note = note[:2000]
        doc.ocr_status = "review" if got_content else "failed"
        db.commit()
    finally:
        db.close()


@router.post("/patients/{patient_id}/documents", response_model=DocumentOut,
             status_code=status.HTTP_201_CREATED)
async def upload_document(
    patient_id: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str = Form("lab"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Document:
    p = _load_patient(db, patient_id)
    _authorize(p, user)                         # patients may upload to their own record
    data = await file.read()
    doc = Document(
        patient_id=p.id, file_path="", original_filename=file.filename or "",
        mime_type=file.content_type or "", size_bytes=len(data),
        doc_type=doc_type if doc_type in ("lab", "imaging", "other") else "lab",
        ocr_status="pending", uploaded_by=user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    doc.file_path = storage.save(doc.id, file.filename or "", data)
    db.commit()
    db.refresh(doc)
    audit.write(db, "document_upload", actor_user_id=user.id, patient_id=p.id,
                detail={"document_id": doc.id, "filename": doc.original_filename})
    background.add_task(run_ocr, doc.id)
    return doc


@router.get("/patients/{patient_id}/documents", response_model=list[DocumentOut])
def list_documents(patient_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)) -> list[Document]:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    return db.query(Document).filter(Document.patient_id == p.id).order_by(Document.created_at.desc()).all()


def _doc_or_404(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)) -> Document:
    doc = _doc_or_404(db, document_id)
    _authorize(db.get(Patient, doc.patient_id), user)
    return doc


@router.get("/documents/{document_id}/file")
def download_document(document_id: str, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    doc = _doc_or_404(db, document_id)
    _authorize(db.get(Patient, doc.patient_id), user)
    return FileResponse(doc.file_path, filename=doc.original_filename or "document")


@router.get("/documents/{document_id}/labs", response_model=list[LabResultOut])
def document_labs(document_id: str, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)) -> list[LabResult]:
    doc = _doc_or_404(db, document_id)
    _authorize(db.get(Patient, doc.patient_id), user)
    return db.query(LabResult).filter(LabResult.document_id == doc.id).order_by(LabResult.analyte).all()


@router.post("/documents/{document_id}/labs/confirm", response_model=list[LabResultOut])
def confirm_labs(document_id: str, body: ConfirmLabsRequest, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)) -> list[LabResult]:
    """STAFF only: edit + confirm the candidate labs for a document. Provided rows become
    confirmed; any leftover unconfirmed candidates for the doc are discarded."""
    if not _is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only staff can confirm labs")
    doc = _doc_or_404(db, document_id)
    keep_ids: set[str] = set()
    for item in body.labs:
        row = db.get(LabResult, item.id) if item.id else None
        if row is None:
            row = LabResult(patient_id=doc.patient_id, document_id=doc.id, source="manual")
            db.add(row)
        row.analyte, row.value, row.unit = item.analyte, item.value, item.unit
        row.ref_low, row.ref_high, row.flag = item.ref_low, item.ref_high, item.flag
        row.confirmed, row.confirmed_by = True, user.id
        db.flush()
        keep_ids.add(row.id)
    for stale in db.query(LabResult).filter(
        LabResult.document_id == doc.id, LabResult.confirmed == False  # noqa: E712
    ).all():
        if stale.id not in keep_ids:
            db.delete(stale)
    doc.ocr_status = "done"
    db.commit()
    audit.write(db, "labs_confirm", actor_user_id=user.id, patient_id=doc.patient_id,
                detail={"document_id": doc.id, "count": len(keep_ids)})
    return db.query(LabResult).filter(LabResult.document_id == doc.id).order_by(LabResult.analyte).all()


@router.get("/patients/{patient_id}/labs", response_model=list[LabResultOut])
def patient_labs(patient_id: str, confirmed: bool | None = None, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)) -> list[LabResult]:
    p = _load_patient(db, patient_id)
    _authorize(p, user)
    q = db.query(LabResult).filter(LabResult.patient_id == p.id)
    if confirmed is not None:
        q = q.filter(LabResult.confirmed == confirmed)
    return q.order_by(LabResult.analyte).all()


@router.post("/patients/{patient_id}/labs", response_model=LabResultOut,
             status_code=status.HTTP_201_CREATED)
def add_manual_lab(patient_id: str, body: LabResultIn, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)) -> LabResult:
    """STAFF manual lab entry (already confirmed) — fallback when OCR can't read a file."""
    if not _is_staff(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only staff can add confirmed labs")
    p = _load_patient(db, patient_id)
    row = LabResult(
        patient_id=p.id, analyte=body.analyte, value=body.value, unit=body.unit,
        ref_low=body.ref_low, ref_high=body.ref_high, flag=body.flag,
        source="manual", confirmed=True, confirmed_by=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    audit.write(db, "lab_manual_add", actor_user_id=user.id, patient_id=p.id)
    return row
