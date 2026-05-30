# =============================================================================
# shm-next — API v1: Billing
# =============================================================================
"""Эндпоинты для биллинга и списаний."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.dependencies import get_billing_service, provide_uow_dependency
from app.core.application.billing.billing_service import BillingService
from app.infrastructure.db.unit_of_work import UnitOfWork


class BillingController(Controller):
    """Контроллер для биллинга."""

    path = "/billing"
    tags = ["Billing"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "billing_service": Provide(get_billing_service, sync_to_thread=False),
    }

    # --- Demo endpoints (string ID support) ---

    @get("/demo/{abonent_id:str}/balance", summary="Баланс абонента (demo)")
    async def get_balance_demo(
        self,
        abonent_id: str,
    ) -> dict:
        """Получить баланс абонента (demo mode)."""
        return {"balance": 1000.0, "currency": "RUB"}

    @get("/demo/{abonent_id:str}/tariff", summary="Тариф абонента (demo)")
    async def get_abonent_tariff_demo(
        self,
        abonent_id: str,
    ) -> dict:
        """Получить информацию о тарифе абонента (demo mode)."""
        return {
            "id": "tariff-1",
            "name": "Основной тариф",
            "price": 500.0,
            "currency": "RUB",
            "description": "Базовый тариф для абонентов",
        }

    @get("/demo/{abonent_id:str}/last-payment", summary="Последний платёж (demo)")
    async def get_last_payment_demo(
        self,
        abonent_id: str,
    ) -> dict:
        """Получить информацию о последнем платеже (demo mode)."""
        return {"id": "pay-1", "amount": 500.0, "status": "paid", "date": "2026-05-20"}

    # --- UUID endpoints ---

    @get("/{abonent_id:uuid}/balance", summary="Баланс абонента")
    async def get_balance(
        self,
        abonent_id: UUID,
        billing_service: BillingService,
    ) -> dict:
        """Получить баланс абонента."""
        try:
            return await billing_service.get_balance(abonent_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    @get("/{abonent_id:uuid}/tariff", summary="Тариф абонента")
    async def get_abonent_tariff(
        self,
        abonent_id: UUID,
        billing_service: BillingService,
    ) -> dict:
        """Получить информацию о тарифе абонента."""
        tariff = await billing_service.get_abonent_tariff_info(abonent_id)
        if tariff is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Tariff for abonent {abonent_id} not found",
            )
        return tariff

    @get("/{abonent_id:uuid}/last-payment", summary="Последний платёж")
    async def get_last_payment(
        self,
        abonent_id: UUID,
        billing_service: BillingService,
    ) -> dict:
        """Получить информацию о последнем платеже."""
        payment = await billing_service.get_abonent_last_payment(abonent_id)
        if payment is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Last payment for abonent {abonent_id} not found",
            )
        return payment

    @post("/{abonent_id:uuid}/withdraw", summary="Списание", status_code=HTTP_201_CREATED)
    async def create_withdraw(
        self,
        abonent_id: UUID,
        uow: UnitOfWork,
        billing_service: BillingService,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> dict:
        """Выполнить списание за услуги."""
        today = date.today()
        start = period_start or today.replace(day=1)
        end = period_end or today
        if end < start:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="period_end must be greater than or equal to period_start",
            )

        withdraws = await billing_service.run_billing_for_abonent(
            abonent_id=abonent_id,
            period_start=start,
            period_end=end,
        )
        await uow.commit()
        return {"withdraws": withdraws}

    @post("/run-cycle", summary="Запуск биллинг-цикла")
    async def run_billing_cycle(
        self,
        uow: UnitOfWork,
        billing_service: BillingService,
        period_start: date | None = None,
        period_end: date | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict:
        """Запустить биллинг-цикл."""
        today = date.today()
        start = period_start or today.replace(day=1)
        end = period_end or today
        if end < start:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="period_end must be greater than or equal to period_start",
            )
        if offset < 0:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="offset must be greater than or equal to 0",
            )
        if limit < 1 or limit > 500:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 500",
            )

        result = await billing_service.run_billing_cycle(
            period_start=start,
            period_end=end,
            offset=offset,
            limit=limit,
        )
        await uow.commit()
        return result
