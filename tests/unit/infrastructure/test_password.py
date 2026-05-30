from app.infrastructure.auth.password import hash_password, verify_password


def test_hash_password_uses_verifiable_hash() -> None:
    password_hash = hash_password("secret-password")

    assert password_hash != "secret-password"
    assert verify_password("secret-password", password_hash)
    assert not verify_password("other-password", password_hash)


def test_verify_password_supports_legacy_demo_hash() -> None:
    assert verify_password("secret-password", "hashed_secret-password")
    assert not verify_password("other-password", "hashed_secret-password")
    assert not verify_password("secret-password", None)
