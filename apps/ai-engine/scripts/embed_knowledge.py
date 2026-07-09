"""Phase 2 loader: embed the knowledge catalog into kb_embeddings (Postgres + pgvector only).

Drops & rebuilds kb_embeddings to the current embedding dimension, then batches the catalog
through the configured EmbeddingProvider (hash or api). Run AFTER seed_db, on Postgres:
    python -m scripts.embed_knowledge
"""
from __future__ import annotations

from app.knowledge.db import IS_POSTGRES, engine, get_session
from app.knowledge.embeddings import EmbeddingProvider
from app.knowledge.models import Axis, Product, SubAxis
from app.knowledge.vectors import get_table

_BATCH = 100


def embed_all() -> dict:
    if not IS_POSTGRES:
        print("SKIP: embeddings require PostgreSQL + pgvector (set DATABASE_URL).")
        return {"embedded": 0}

    emb = EmbeddingProvider()
    table = get_table(emb.dim)
    eng = engine()
    table.drop(eng, checkfirst=True)     # rebuild to match current dimension/backend
    table.create(eng, checkfirst=True)

    s = get_session()
    try:
        rows: list[tuple[str, str, str]] = []  # (kind, ref_code, content)
        for a in s.query(Axis).all():
            subs = " ".join(x.description for x in s.query(SubAxis).filter_by(axis_id=a.id))
            rows.append(("axis", a.code, f"{a.code} {a.name}. {subs}"))
        for p in s.query(Product).all():
            rows.append(("product", str(p.tspi_id or p.name), p.name or ""))

        n = 0
        for i in range(0, len(rows), _BATCH):
            chunk = rows[i:i + _BATCH]
            vecs = emb.embed_many([c[2] for c in chunk])
            s.execute(table.insert(), [
                {"kind": k, "ref_code": rc, "content": ct, "embedding": v}
                for (k, rc, ct), v in zip(chunk, vecs)
            ])
            n += len(chunk)
        s.commit()
        return {"embedded": n, "backend": emb.backend, "dim": emb.dim}
    finally:
        s.close()


if __name__ == "__main__":
    print("embedded:", embed_all())
