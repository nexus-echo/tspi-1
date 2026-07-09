"""MiHealth API entrypoint. Phase A: auth + admin users. Phase B: patients/intake/consent.

The brain (tspi_ai_brain) is consumed as a service at settings.tspi_base_url; this service
holds all PII and de-identifies before calling TSPI (wired in a later phase)."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Role, User
from app.routers import auth, documents, learning, patients, reports, users
from app.security import hash_password


def seed_admin() -> None:
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(
                User(
                    email=settings.seed_admin_email,
                    password_hash=hash_password(settings.seed_admin_password),
                    role=Role.admin,
                    full_name=settings.seed_admin_name,
                )
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # prototype; replace with Alembic later
    seed_admin()
    yield


app = FastAPI(title="MiHealth API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(documents.router)
app.include_router(reports.router)
app.include_router(learning.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "service": "mihealth", "tspi_base_url": settings.tspi_base_url}
