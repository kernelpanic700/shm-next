import jwt
import pytest

from app.api.config import AppConfig
from app.infrastructure.auth.jwt import JWTManager


def test_jwt_decode_requires_expected_issuer() -> None:
    config = AppConfig(secret_key="test-secret-key-with-at-least-32-bytes", _env_file=None)
    token = jwt.encode(
        {
            "sub": "user-1",
            "type": "access",
            "session_id": "session-1",
            "permissions": [],
            "exp": 4102444800,
            "iat": 1704067200,
            "iss": "other-service",
        },
        config.secret_key,
        algorithm=config.algorithm,
    )

    with pytest.raises(jwt.InvalidIssuerError):
        JWTManager(config).decode(token)


def test_jwt_decode_requires_core_claims() -> None:
    config = AppConfig(secret_key="test-secret-key-with-at-least-32-bytes", _env_file=None)
    token = jwt.encode(
        {
            "sub": "user-1",
            "type": "access",
            "permissions": [],
            "exp": 4102444800,
            "iat": 1704067200,
            "iss": "shm-next",
        },
        config.secret_key,
        algorithm=config.algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        JWTManager(config).decode(token)
