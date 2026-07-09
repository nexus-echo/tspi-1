"""Password hashing + JWT issue/verify.

Uses the `bcrypt` library directly (not passlib) to avoid passlib's self-test crashing on
bcrypt 5.x. bcrypt only considers the first 72 bytes, so we truncate explicitly (the documented
behaviour) for both hashing and verification.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

_BCRYPT_MAX = 72


def _prepare(raw: str) -> bytes:
    return raw.encode("utf-8")[:_BCRYPT_MAX]


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(_prepare(raw), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(raw), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _make_token(sub: str, role: str, kind: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "role": role, "type": kind, "iat": now, "exp": now + expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def make_access_token(user_id: str, role: str) -> str:
    return _make_token(user_id, role, "access", timedelta(minutes=settings.access_token_minutes))


def make_refresh_token(user_id: str, role: str) -> str:
    return _make_token(user_id, role, "refresh", timedelta(days=settings.refresh_token_days))


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
