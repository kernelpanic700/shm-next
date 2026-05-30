"""Password hashing helpers."""

from __future__ import annotations

import hashlib
from hmac import compare_digest

import bcrypt


_HASH_PREFIX = "bcrypt_sha256$"


def _normalize_password(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    password_hash = bcrypt.hashpw(_normalize_password(password), bcrypt.gensalt())
    return f"{_HASH_PREFIX}{password_hash.decode('ascii')}"


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a plain-text password against supported hash formats."""
    if not password_hash:
        return False

    if password_hash.startswith(_HASH_PREFIX):
        stored_hash = password_hash.removeprefix(_HASH_PREFIX).encode("ascii")
        return bcrypt.checkpw(_normalize_password(password), stored_hash)

    if password_hash.startswith("$2"):
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))

    # Backward compatibility for accounts created by earlier demo code.
    if password_hash.startswith("hashed_"):
        return compare_digest(password_hash, f"hashed_{password}")

    return False
