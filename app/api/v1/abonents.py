# =============================================================================
# shm-next — Abonent API Router
# =============================================================================
"""
Роутер для управления абонентами.
"""

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from app.api.dependencies import get_abonent_service, provide_uow_dependency
from app.api.dto.requests import AbonentCreateRequest, AbonentUpdateRequest, BalanceTopUpRequest
from app.api.dto.responses import AbonentListResponse, AbonentResponse
from app.core.application.abonents.abonent_service import AbonentService
from app.core.domain.entities.abonent import AbonentCreate, AbonentUpdate
from app.infrastructure.db.unit_of_work import UnitOfWork


class AbonentController(Controller):
    """Контроллер для управления абонентами."""
    path = "/abonents"
    tags = ["Abonents"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "abonent_service": Provide(get_abonent_service, sync_to_thread=False),
    }

    @get(
        path="/",
        summary="Получить список абонентов с фильтрацией и пагинацией",
        response_model=AbonentListResponse,
        status_code=HTTP_200_OK,
    )
    async def list_abonents(
        self,
        abonent_service: AbonentService,
        page: int = 1,
        size: int = 20,
        status: str | None = Parameter(query="status", required=False),
        tariff_id: UUID | None = Parameter(query="tariff_id", required=False),
        min_balance: float | None = Parameter(query="min_balance", required=False),
        max_balance: float | None = Parameter(query="max_balance", required=False),
    ) -> AbonentListResponse:
        """Получить список абонентов с поддержкой фильтрации и пагинации."""
        offset = (page - 1) * size
        abonents = await abonent_service.list_abonents(
            offset=offset,
            limit=size,
            status=status,
            tariff_id=tariff_id,
            min_balance=min_balance,
            max_balance=max_balance,
        )
        total = len(abonents)  # Note: This should ideally be a separate count query
        pages = (total + size - 1) // size if total > 0 else 0
        return AbonentListResponse(
            items=[AbonentResponse.model_validate(a, from_attributes=True) for a in abonents],
            total=total,
            page=page,
            per_page=size,
            pages=pages,
        )

    @get(
        path="/{abonent_id:uuid}",
        summary="Получить абонента по ID",
        response_model=AbonentResponse,
        status_code=HTTP_200_OK,
    )
    async def get_abonent(
        self,
        abonent_id: UUID,
        abonent_service: AbonentService,
    ) -> AbonentResponse:
        """Получить абонента по его идентификатору."""
        abonent = await abonent_service.get_abonent(abonent_id)
        if not abonent:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Abonent with id {abonent_id} not found",
            )
        return AbonentResponse.model_validate(abonent, from_attributes=True)

    @get(
        path="/phone/{phone:str}",
        summary="Поиск по телефону",
        description="Найти абонента по номеру телефона",
    )
    async def get_by_phone(
        self,
        phone: str,
        abonent_service: AbonentService,
    ) -> AbonentResponse:
        """Найти абонента по номеру телефона."""
        abonent = await abonent_service.get_abonent_by_phone(phone)
        if not abonent:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Abonent with phone {phone} not found",
            )
        return AbonentResponse.model_validate(abonent, from_attributes=True)

    @get(
        path="/account/{account_number:str}",
        summary="Поиск по лицевому счёту",
        description="Найти абонента по номеру лицевого счёта",
    )
    async def get_by_account(
        self,
        account_number: str,
        abonent_service: AbonentService,
    ) -> AbonentResponse:
        """Найти абонента по номеру лицевого счёта."""
        abonent = await abonent_service.get_abonent_by_account(account_number)
        if not abonent:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Abonent with account number {account_number} not found",
            )
        return AbonentResponse.model_validate(abonent, from_attributes=True)

    @post(
        path="/",
        summary="Создать нового абонента",
        response_model=AbonentResponse,
        status_code=HTTP_201_CREATED,
    )
    async def create_abonent(
        self,
        data: AbonentCreateRequest,
        uow: UnitOfWork,
        abonent_service: AbonentService,
    ) -> AbonentResponse:
        """Создать нового абонента."""
        async with uow:
            try:
                saved = await abonent_service.create_abonent(
                    AbonentCreate(
                        full_name=data.full_name,
                        phone=data.phone,
                        account_number=data.account_number,
                        balance=data.balance,
                        currency=data.currency,
                        allow_negative=data.allow_negative,
                        tariff_id=data.tariff_id,
                        metadata=data.metadata,
                    )
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=str(exc),
                ) from exc
            await uow.commit()
            return AbonentResponse.model_validate(saved, from_attributes=True)

    @patch(
        path="/{abonent_id:uuid}",
        summary="Обновить абонента частично",
        response_model=AbonentResponse,
        status_code=HTTP_200_OK,
    )
    async def update_abonent(
        self,
        abonent_id: UUID,
        data: AbonentUpdateRequest,
        uow: UnitOfWork,
        abonent_service: AbonentService,
    ) -> AbonentResponse:
        """Обновить абонента частично (PATCH)."""
        async with uow:
            try:
                saved = await abonent_service.update_abonent(
                    abonent_id,
                    AbonentUpdate(
                        full_name=data.full_name,
                        phone=data.phone,
                        status=data.status,
                        tariff_id=data.tariff_id,
                        allow_negative=data.allow_negative,
                        metadata=data.metadata,
                    ),
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=str(exc),
                ) from exc
            if not saved:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Abonent with id {abonent_id} not found",
                )
            await uow.commit()
            return AbonentResponse.model_validate(saved, from_attributes=True)

    @delete(
        path="/{abonent_id:uuid}",
        summary="Удалить абонента (мягкое удаление)",
        status_code=HTTP_204_NO_CONTENT,
    )
    async def delete_abonent(
        self,
        abonent_id: UUID,
        uow: UnitOfWork,
        abonent_service: AbonentService,
    ) -> None:
        """Удалить абонента (изменить статус на INACTIVE)."""
        async with uow:
            saved = await abonent_service.deactivate_abonent(abonent_id)
            if not saved:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Abonent with id {abonent_id} not found",
                )
            await uow.commit()
            return None

    @post(
        path="/{abonent_id:uuid}/balance/top-up",
        summary="Пополнить баланс абонента",
        response_model=AbonentResponse,
        status_code=HTTP_200_OK,
    )
    async def top_up_balance(
        self,
        abonent_id: UUID,
        data: BalanceTopUpRequest,
        uow: UnitOfWork,
        abonent_service: AbonentService,
    ) -> AbonentResponse:
        """Пополнить баланс абонента на указанную сумму."""
        async with uow:
            try:
                saved = await abonent_service.change_balance(
                    abonent_id,
                    amount=float(data.amount),
                    currency="RUB",
                    reason=f"Manual top-up via {data.payment_method}",
                )
            except ValueError as exc:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=str(exc),
                ) from exc
            await uow.commit()
            return AbonentResponse.model_validate(saved, from_attributes=True)
