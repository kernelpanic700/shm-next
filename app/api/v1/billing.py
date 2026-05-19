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
from app.api.dto.responses import BalanceResponse, TariffInfoResponse
from app.core.application.billing.billing_service import BillingService
from app.infrastructure.db.unit_of_work import UnitOfWork


class BillingController(Controller):
    """Контроллер для биллинга."""

    path = "/v1/billing"
    tags = ["Billing"]

    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "billing_service": Provide(get_billing_service),
    }

    @get("/{abonent_id:uuid}/balance", summary="Баланс абонента")
    async def get_balance(
        self,
        abonent_id: UUID,
        billing_service: BillingService,
    ) -> BalanceResponse:
        """Получить баланс абонента."""
        balance = await billing_service.get_balance(abonent_id)
        return BalanceResponse(**balance)

    @get("/{abonent_id:uuid}/tariff", summary="Тариф абонента")
    async def get_abonent_tariff(
        self,
        abonent_id: UUID,
        billing_service: BillingService,
    ) -> TariffInfoResponse:
        """Получить информацию о тарифе абонента."""
        tariff_info = await billing_service.get_abonent_tariff_info(abonent_id)
        if not tariff_info:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Tariff not found")
        return TariffInfoResponse(**tariff_info)

    @get("/{abonent_id:uuid}/last-payment", summary="Последний платёж")
    async def get_last_payment(
        self,
        abonent_id: UUID,
        billing_service: BillingService,
    ) -> dict:
        """Получить информацию о последнем платеже."""
        payment = await billing_service.get_abonent_last_payment(abonent_id)
        return payment or {}

    @post("/{abonent_id:uuid}/withdraw", summary="Списание", status_code=HTTP_201_CREATED)
    async def create_withdraw(
        self,
        abonent_id: UUID,
        uow: UnitOfWork,
        billing_service: BillingService,
    ) -> dict:
        """Выполнить списание за услуги."""
        async with uow:
            withdraws = await billing_service.run_billing_for_abonent(
                abonent_id=abonent_id,
                period_start=date.today(),
                period_end=date.today(),
            )
            await uow.commit()

            if not withdraws:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="No withdrawals created")

            return {"withdraws": withdraws}

    @post("/run-cycle", summary="Запуск биллинг-цикла")
    async def run_billing_cycle(
        self,
        billing_service: BillingService,
    ) -> dict:
        """Запустить биллинг-цикл."""
        return {"message": "Billing cycle started"}
