"""App-level encryption for PII columns ("encrypted at rest").

A SQLAlchemy TypeDecorator that transparently encrypts strings with Fernet
(AES-128-CBC + HMAC). The key is derived from settings so the prototype runs
out of the box; override PII_ENCRYPTION_KEY (or JWT_SECRET) for real use.

Reads tolerate legacy plaintext (decrypt failure -> return raw), so enabling
encryption on an existing dev DB does not break.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, TypeDecorator

from app.config import settings


def _fernet() -> Fernet:
    secret = (settings.pii_encryption_key or settings.jwt_secret).encode("utf-8")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())  # valid 32-byte Fernet key
    return Fernet(key)


class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return _fernet().encrypt(str(value).encode("utf-8")).decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
        except (InvalidToken, ValueError, AttributeError):
            return value  # tolerate pre-existing plaintext
