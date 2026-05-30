from datetime import UTC, datetime
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import PaymentCreate
from app.api.v1.payments import PaymentController
from app.core.domain.entities.payment import Payment
from app.core.domain.value_objects import PaymentStatus


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        self.close_count += 1

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class FakeRequest:
    def __init__(self, user_id: str | None = None, permissions: list[str] | None = None) -> None:
        self.scope = {"state": {"user_id": user_id, "permissions": permissions or []}}


def admin_request() -> FakeRequest:
    return FakeRequest("admin:+79990000000", ["*"])


class FakePaymentService:
    def __init__(self) -> None:
        self.payment = Payment(
            id=uuid4(),
            abonent_id=uuid4(),
            amount=500,
            currency="RUB",
            payment_method="card",
            status=PaymentStatus.NEW,
        )
        self.create_calls: list[tuple] = []
        self.confirm_calls: list = []
        self.refund_calls: list = []

    def _payment_dict(self) -> dict:
        return {
            "id": self.payment.id,
            "abonent_id": self.payment.abonent_id,
            "amount": self.payment.amount,
            "currency": self.payment.currency,
            "payment_method": self.payment.payment_method,
            "status": self.payment.status.value,
            "external_id": self.payment.external_id,
            "created_at": self.payment.created_at,
            "completed_at": self.payment.completed_at,
        }

    async def get_all_payments(self, from_date=None, to_date=None, limit=50):
        return [self._payment_dict()]

    async def get_payments_by_abonent(self, abonent_id, from_date=None, to_date=None, limit=50):
        return [self._payment_dict()] if abonent_id == self.payment.abonent_id else []

    async def get_payment(self, payment_id):
        return self._payment_dict() if payment_id == self.payment.id else None

    async def create_payment(self, abonent_id, amount, currency, payment_method, external_id=None):
        self.create_calls.append((abonent_id, amount, currency, payment_method, external_id))
        if amount == 999:
            raise ValueError(f"Abonent {abonent_id} not found")
        self.payment = Payment(
            id=uuid4(),
            abonent_id=abonent_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            external_id=external_id,
            status=PaymentStatus.NEW,
            created_at=datetime.now(UTC),
        )
        return self.payment

    async def confirm_payment(self, payment_id):
        self.confirm_calls.append(payment_id)
        if payment_id != self.payment.id:
            return False
        self.payment.confirm()
        return True

    async def refund_payment(self, payment_id):
        self.refund_calls.append(payment_id)
        if payment_id != self.payment.id:
            return False
        self.payment.refund()
        return True


@pytest.mark.asyncio
async def test_create_payment_passes_method_and_external_id() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()
    request = PaymentCreate(
        abonent_id=uuid4(),
        amount=250,
        currency="RUB",
        payment_method="terminal",
        external_id="ext-1",
    )

    response = await PaymentController.create_payment.fn(
        None,
        request=admin_request(),
        data=request,
        uow=uow,
        payment_service=payment_service,
    )

    assert response.payment_method == "terminal"
    assert response.external_id == "ext-1"
    assert payment_service.create_calls == [
        (request.abonent_id, 250, "RUB", "terminal", "ext-1")
    ]
    assert uow.commit_count == 2


@pytest.mark.asyncio
async def test_create_payment_returns_404_when_abonent_missing() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()
    request = PaymentCreate(abonent_id=uuid4(), amount=999)

    with pytest.raises(HTTPException) as exc_info:
        await PaymentController.create_payment.fn(
            None,
            request=admin_request(),
            data=request,
            uow=uow,
            payment_service=payment_service,
        )

    assert exc_info.value.status_code == 404
    assert uow.rollback_count == 1


@pytest.mark.asyncio
async def test_create_payment_rejects_abonent_for_different_abonent() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()
    current_abonent_id = uuid4()
    request = PaymentCreate(abonent_id=uuid4(), amount=250)

    with pytest.raises(HTTPException) as exc_info:
        await PaymentController.create_payment.fn(
            None,
            request=FakeRequest(str(current_abonent_id), ["self:read", "payments:read"]),
            data=request,
            uow=uow,
            payment_service=payment_service,
        )

    assert exc_info.value.status_code == 403
    assert payment_service.create_calls == []
    assert uow.commit_count == 0


@pytest.mark.asyncio
async def test_list_payments_rejects_abonent_without_self_filter() -> None:
    payment_service = FakePaymentService()

    with pytest.raises(HTTPException) as exc_info:
        await PaymentController.list_payments.fn(
            None,
            request=FakeRequest(str(payment_service.payment.abonent_id), ["self:read", "payments:read"]),
            payment_service=payment_service,
            abonent_id=None,
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_list_payments_allows_abonent_self_filter() -> None:
    payment_service = FakePaymentService()

    response = await PaymentController.list_payments.fn(
        None,
        request=FakeRequest(str(payment_service.payment.abonent_id), ["self:read", "payments:read"]),
        payment_service=payment_service,
        abonent_id=payment_service.payment.abonent_id,
    )

    assert response.total == 1


@pytest.mark.asyncio
async def test_confirm_payment_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()

    response = await PaymentController.confirm_payment.fn(
        None,
        payment_id=payment_service.payment.id,
        uow=uow,
        payment_service=payment_service,
    )

    assert response.status == "COMPLETED"
    assert payment_service.confirm_calls == [payment_service.payment.id]
    assert uow.commit_count == 2


@pytest.mark.asyncio
async def test_confirm_payment_returns_404_when_missing() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()

    with pytest.raises(HTTPException) as exc_info:
        await PaymentController.confirm_payment.fn(
            None,
            payment_id=uuid4(),
            uow=uow,
            payment_service=payment_service,
        )

    assert exc_info.value.status_code == 404
    assert uow.rollback_count == 1


@pytest.mark.asyncio
async def test_refund_payment_commits_unit_of_work() -> None:
    uow = FakeUnitOfWork()
    payment_service = FakePaymentService()
    payment_service.payment.confirm()

    response = await PaymentController.refund_payment.fn(
        None,
        payment_id=payment_service.payment.id,
        uow=uow,
        payment_service=payment_service,
    )

    assert response.status == "REFUNDED"
    assert payment_service.refund_calls == [payment_service.payment.id]
    assert uow.commit_count == 2
