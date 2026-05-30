import json
from uuid import uuid4

import pytest

from app.api.middleware.auth import AuthMiddleware
from app.infrastructure.auth.jwt import JWTManager


async def _run_middleware(scope: dict) -> tuple[list[dict], dict]:
    messages: list[dict] = []

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await AuthMiddleware()(app)(scope, receive, send)
    return messages, scope


@pytest.mark.asyncio
async def test_auth_middleware_allows_public_paths() -> None:
    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/auth/login",
            "method": "POST",
            "headers": [],
            "state": {},
        }
    )

    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_auth_middleware_rejects_missing_bearer_token() -> None:
    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/payments/",
            "method": "GET",
            "headers": [],
            "state": {},
        }
    )

    assert messages[0]["status"] == 401
    body = json.loads(messages[1]["body"])
    assert body["success"] is False
    assert body["error"]["message"] == "Missing or invalid authorization header"


@pytest.mark.asyncio
async def test_auth_middleware_sets_request_state_from_access_token() -> None:
    token = JWTManager().create_access_token(
        subject="user-1",
        session_id="session-1",
        permissions=["self:read"],
    )

    messages, scope = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/auth/me",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 204
    assert scope["state"]["user_id"] == "user-1"
    assert scope["state"]["session_id"] == "session-1"
    assert scope["state"]["permissions"] == ["self:read"]


@pytest.mark.asyncio
async def test_auth_middleware_rejects_abonent_token_for_admin_api() -> None:
    token = JWTManager().create_access_token(
        subject="user-1",
        session_id="session-1",
        permissions=["self:read", "payments:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/abonents/",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 403
    body = json.loads(messages[1]["body"])
    assert body["error"]["message"] == "Permission denied"


@pytest.mark.asyncio
async def test_auth_middleware_allows_admin_token_for_admin_api() -> None:
    token = JWTManager().create_access_token(
        subject="admin:+79990000000",
        session_id="session-1",
        permissions=["*"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/abonents/",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_auth_middleware_allows_abonent_self_scoped_billing_read() -> None:
    abonent_id = uuid4()
    token = JWTManager().create_access_token(
        subject=str(abonent_id),
        session_id="session-1",
        permissions=["self:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": f"/api/v1/billing/{abonent_id}/balance",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_auth_middleware_rejects_abonent_other_scoped_billing_read() -> None:
    token = JWTManager().create_access_token(
        subject=str(uuid4()),
        session_id="session-1",
        permissions=["self:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": f"/api/v1/billing/{uuid4()}/balance",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 403


@pytest.mark.asyncio
async def test_auth_middleware_rejects_demo_endpoints_for_abonent_token() -> None:
    token = JWTManager().create_access_token(
        subject=str(uuid4()),
        session_id="session-1",
        permissions=["self:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/services/demo/test-user/",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 403


@pytest.mark.asyncio
async def test_auth_middleware_rejects_abonent_payment_admin_actions() -> None:
    token = JWTManager().create_access_token(
        subject=str(uuid4()),
        session_id="session-1",
        permissions=["self:read", "payments:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": f"/api/v1/payments/{uuid4()}/confirm",
            "method": "POST",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 403


@pytest.mark.asyncio
async def test_auth_middleware_allows_abonent_payment_create_to_controller_scope_check() -> None:
    token = JWTManager().create_access_token(
        subject=str(uuid4()),
        session_id="session-1",
        permissions=["self:read", "payments:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/payments/",
            "method": "POST",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_auth_middleware_allows_abonent_payment_read_to_controller_scope_check() -> None:
    token = JWTManager().create_access_token(
        subject=str(uuid4()),
        session_id="session-1",
        permissions=["self:read", "payments:read"],
    )

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/payments/",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 204


@pytest.mark.asyncio
async def test_auth_middleware_rejects_refresh_token_for_api_access() -> None:
    token = JWTManager().create_refresh_token(subject="user-1", session_id="session-1")

    messages, _ = await _run_middleware(
        {
            "type": "http",
            "path": "/api/v1/payments/",
            "method": "GET",
            "headers": [(b"authorization", f"Bearer {token}".encode("latin-1"))],
            "state": {},
        }
    )

    assert messages[0]["status"] == 401
    body = json.loads(messages[1]["body"])
    assert body["error"]["message"] == "Invalid token type"
