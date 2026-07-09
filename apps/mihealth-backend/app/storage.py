"""Local-disk file storage for the prototype (mount a volume in Docker; swap for S3 later)."""
from __future__ import annotations

import os

from app.config import settings


def _dir() -> str:
    os.makedirs(settings.upload_dir, exist_ok=True)
    return settings.upload_dir


def save(doc_id: str, filename: str, data: bytes) -> str:
    ext = os.path.splitext(filename or "")[1]
    path = os.path.join(_dir(), f"{doc_id}{ext}")
    with open(path, "wb") as fh:
        fh.write(data)
    return path
