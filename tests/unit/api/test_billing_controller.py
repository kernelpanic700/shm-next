from datetime import date
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.v1.billing import BillingController


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0

    async def commit(self) -> None:
        self.commit_count += 1


class FakeBillingService:
    def __init__(self) -> None:
        self.abonent_id = uuid4()
        self.withdraw_calls: list[dict] = []
        self.cycle_calls: list[dict] = []
        self.balance = {
            "balance": 1500.0,
            "currency": "RUB",
            "available": True,
            "allow_negative": False,
        }
        self.tariff = {
            "id": str(uuid4()),
            "name": "Base",
            "price": 500.0,
            "currency": "RUB",
            "billing_period": "monthly",
            "services": [],
        }
        self.payment = {
            "id": str(uuid4()),
            "amount": 500.0,
            "currency": "RUB",
            "status": "COMPLETED",
        }

    async def get_balance(self, abonent_id):
        if abonent_id != self.abonent_id:
            raise ValueError(f"Abonent {abonent_id} not found")
        return self.balance

    async def get_abonent_tariff_info(self, abonent_id):
        return self.tariff if abonent_id == self.abonent_id else None

    async def get_abonent_last_payment(self, abonent_id):
        return self.payment if abonent_id == self.abonent_id else None

    async def run_billing_for_abonent(self, **kwargs):
        self.withdraw_calls.append(kwargs)
        return [
            {
                "withdraw_id": uuid4(),
                "service_id": uuid4(),
                "amount": 100.0,
                "currency": "RUB",
            }
        ]

    async def run_billing_cycle(self, **kwargs):
        self.cycle_calls.append(kwargs)
        return {
            "period_start": kwargs["period_start"],
            "period_end": kwargs["period_end"],
            "offset": kwargs["offset"],
            "limit": kwargs["limit"],
            "processed": 1,
            "withdraw_count": 1,
            "invoice_count": 1,
            "items": [],
        }


@pytest.mark.asyncio
async def test_get_balance_uses_billing_service() -> None:
    service = FakeBillingService()

    response = await BillingController.get_balance.fn(
        None,
        abonent_id=service.abonent_id,
        billing_service=service,
    )

    assert response["balance"] == 1500.0
    assert response["available"] is True


@pytest.mark.asyncio
async def test_get_balance_returns_404_when_abonent_missing() -> None:
    service = FakeBillingService()

    with pytest.raises(HTTPException) as exc_info:
        await BillingController.get_balance.fn(
            None,
            abonent_id=uuid4(),
            billing_service=service,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_tariff_returns_404_when_missing() -> None:
    service = FakeBillingService()

    with pytest.raises(HTTPException) as exc_info:
        await BillingController.get_abonent_tariff.fn(
            None,
            abonent_id=uuid4(),
            billing_service=service,
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_last_payment_uses_billing_service() -> None:
    service = FakeBillingService()

    response = await BillingController.get_last_payment.fn(
        None,
        abonent_id=service.abonent_id,
        billing_service=service,
    )

    assert response["amount"] == 500.0


@pytest.mark.asyncio
async def test_create_withdraw_runs_billing_and_commits() -> None:
    uow = FakeUnitOfWork()
    service = FakeBillingService()

    response = await BillingController.create_withdraw.fn(
        None,
        abonent_id=service.abonent_id,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 27),
        uow=uow,
        billing_service=service,
    )

    assert uow.commit_count == 1
    assert len(response["withdraws"]) == 1
    assert service.withdraw_calls == [
        {
            "abonent_id": service.abonent_id,
            "period_start": date(2026, 5, 1),
            "period_end": date(2026, 5, 27),
        }
    ]


@pytest.mark.asyncio
async def test_create_withdraw_rejects_invalid_period() -> None:
    service = FakeBillingService()

    with pytest.raises(HTTPException) as exc_info:
        await BillingController.create_withdraw.fn(
            None,
            abonent_id=service.abonent_id,
            period_start=date(2026, 5, 27),
            period_end=date(2026, 5, 1),
            uow=FakeUnitOfWork(),
            billing_service=service,
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_run_billing_cycle_runs_service_and_commits() -> None:
    uow = FakeUnitOfWork()
    service = FakeBillingService()

    response = await BillingController.run_billing_cycle.fn(
        None,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 5, 27),
        offset=5,
        limit=10,
        uow=uow,
        billing_service=service,
    )

    assert uow.commit_count == 1
    assert response["processed"] == 1
    assert response["invoice_count"] == 1
    assert service.cycle_calls == [
        {
            "period_start": date(2026, 5, 1),
            "period_end": date(2026, 5, 27),
            "offset": 5,
            "limit": 10,
        }
    ]


@pytest.mark.asyncio
async def test_run_billing_cycle_rejects_invalid_limit() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await BillingController.run_billing_cycle.fn(
            None,
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 27),
            offset=0,
            limit=0,
            uow=FakeUnitOfWork(),
            billing_service=FakeBillingService(),
        )

    assert exc_info.value.status_code == 400
