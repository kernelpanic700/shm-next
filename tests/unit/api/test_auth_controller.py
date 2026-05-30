import pytest
from litestar.datastructures import State
from litestar.exceptions import HTTPException

from app.api.dto.requests import LoginRequest, RegisterRequest
from app.api.config import AppConfig, reset_config_cache
from app.api.v1.auth import AuthController
from app.core.domain.entities.abonent import Abonent
from app.core.domain.value_objects import Money
from app.infrastructure.auth.password import hash_password, verify_password


class FakeAbonentRepository:
    def __init__(self, abonent: Abonent | None = None) -> None:
        self.abonent = abonent
        self.saved: Abonent | None = None

    async def get_by_phone(self, phone: str) -> Abonent | None:
        if self.abonent and self.abonent.phone == phone:
            return self.abonent
        return None

    async def get(self, abonent_id) -> Abonent | None:
        if self.abonent and self.abonent.id == abonent_id:
            return self.abonent
        return None

    async def save(self, abonent: Abonent) -> Abonent:
        self.saved = abonent
        self.abonent = abonent
        return abonent


class FakeUnitOfWork:
    def __init__(self, abonent: Abonent | None = None) -> None:
        self.abonents = FakeAbonentRepository(abonent)
        self.commit_count = 0
        self.rollback_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


def make_abonent(password: str = "secret-password") -> Abonent:
    return Abonent(
        full_name="Test User",
        phone="+79990000001",
        account_number="ACC001",
        balance=Money(100, "RUB"),
        password_hash=hash_password(password),
    )


class FakeRequest:
    def __init__(self, user_id: str | None) -> None:
        self.scope = {"state": {"user_id": user_id} if user_id else {}}


@pytest.mark.asyncio
async def test_login_rejects_unknown_phone() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await AuthController.login.fn(
            None,
            data=LoginRequest(phone="+79990000001", password="secret-password"),
            uow=FakeUnitOfWork(),
            state=State(),
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_wrong_password() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await AuthController.login.fn(
            None,
            data=LoginRequest(phone="+79990000001", password="wrong-password"),
            uow=FakeUnitOfWork(make_abonent()),
            state=State(),
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_issues_tokens_for_valid_password() -> None:
    response = await AuthController.login.fn(
        None,
        data=LoginRequest(phone="+79990000001", password="secret-password"),
        uow=FakeUnitOfWork(make_abonent()),
        state=State(),
    )

    assert response.success is True
    assert response.data["access_token"]
    assert response.data["refresh_token"]
    assert response.data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_issues_admin_permissions_for_bootstrap_admin(monkeypatch) -> None:
    import app.api.config as config_module

    monkeypatch.setattr(
        config_module,
        "_config_cache",
        AppConfig(_env_file=None, admin_phone="+79990000009", admin_password="admin-secret", admin_password_hash=""),
    )
    try:
        response = await AuthController.login.fn(
            None,
            data=LoginRequest(phone="+79990000009", password="admin-secret"),
            uow=FakeUnitOfWork(),
            state=State(),
        )
    finally:
        reset_config_cache()

    assert response.success is True
    assert response.data["access_token"]


@pytest.mark.asyncio
async def test_me_returns_current_authenticated_abonent() -> None:
    abonent = make_abonent()

    response = await AuthController.me.fn(
        None,
        request=FakeRequest(str(abonent.id)),
        uow=FakeUnitOfWork(abonent),
    )

    assert response.success is True
    assert response.data["id"] == abonent.id
    assert response.data["phone"] == abonent.phone


@pytest.mark.asyncio
async def test_me_requires_authenticated_user() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await AuthController.me.fn(
            None,
            request=FakeRequest(None),
            uow=FakeUnitOfWork(),
        )

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_register_stores_bcrypt_password_hash() -> None:
    uow = FakeUnitOfWork()

    response = await AuthController.register.fn(
        None,
        data=RegisterRequest(
            full_name="New User",
            phone="+79990000002",
            email=None,
            password="secret-password",
        ),
        uow=uow,
        state=State(),
    )

    assert response.success is True
    assert uow.abonents.saved is not None
    assert uow.abonents.saved.password_hash != "hashed_secret-password"
    assert verify_password("secret-password", uow.abonents.saved.password_hash)
