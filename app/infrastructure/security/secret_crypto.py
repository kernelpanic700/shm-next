# =============================================================================
# shm-next - Secret encryption helpers
# =============================================================================
from __future__ import annotations

import base64

from app.api.config import get_app_config

_PREFIX = "enc:v1:"


def _fernet():
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    except ImportError as exc:
        raise RuntimeError("cryptography is required to encrypt stored secrets") from exc

    config = get_app_config()
    material = config.secret_key.encode("utf-8")
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"shm-next-secret-crypto-v1",
        info=b"ssh-key-encryption",
    ).derive(material)
    return Fernet(base64.urlsafe_b64encode(key))


def is_encrypted(value: str | None) -> bool:
    return bool(value and value.startswith(_PREFIX))


def encrypt_secret(value: str | None) -> str | None:
    if value is None or value == "" or is_encrypted(value):
        return value
    token = _fernet().encrypt(value.encode("utf-8")).decode("ascii")
    return f"{_PREFIX}{token}"


def decrypt_secret(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    if not is_encrypted(value):
        return value
    token = value[len(_PREFIX):].encode("ascii")
    return _fernet().decrypt(token).decode("utf-8")
