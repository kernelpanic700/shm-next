# =============================================================================
# shm-next — Abonent API Router
# =============================================================================
"""
Роутер для управления абонентами.
"""

from __future__ import annotations

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
from app.core.domain.value_objects import AbonentStatus
from app.infrastructure.db.unit_of_work import UnitOfWork


class AbonentController(Controller):
    """Контроллер для управления абонентами."""
    path = "/v1/abonents"
    tags = ["Abonents"]
    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "abonent_service": Provide(get_abonent_service),
    }

    @get(
        path="/",
        summary="Получить список абонентов с фильтрацией и пагинацией",
        response_model=AbonentListResponse,
        status_code=HTTP_200_OK,
    )
    async def list_abonents(
        self,
        uow: UnitOfWork,
        page: int = 1,
        size: int = 20,
        status: str | None = Parameter(query="status", required=False),
        tariff_id: UUID | None = Parameter(query="tariff_id", required=False),
        min_balance: float | None = Parameter(query="min_balance", required=False),
        max_balance: float | None = Parameter(query="max_balance", required=False),
    ) -> AbonentListResponse:
        """Получить список абонентов с поддержкой фильтрации и пагинации."""
        offset = (page - 1) * size
        abonents = await uow.abonents.list(
            offset=offset,
            limit=size,
            status=status,
        )
        total = len(abonents)  # Note: This should ideally be a separate count query
        pages = (total + size - 1) // size if total > 0 else 0
        return AbonentListResponse(
            items=[AbonentResponse.model_validate(a, from_attributes=True) for a in abonents],
            total=total,
            page=page,
            size=size,
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
        uow: UnitOfWork,
    ) -> AbonentResponse:
        """Получить абонента по его идентификатору."""
        abonent = await uow.abonents.get(abonent_id)
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
        uow: UnitOfWork,
    ) -> AbonentResponse:
        """Найти абонента по номеру телефона."""
        abonent = await uow.abonents.get_by_phone(phone)
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
        uow: UnitOfWork,
    ) -> AbonentResponse:
        """Найти абонента по номеру лицевого счёта."""
        abonent = await uow.abonents.get_by_account(account_number)
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
    ) -> AbonentResponse:
        """Создать нового абонента."""
        async with uow:
            from app.core.domain.entities.abonent import Abonent
            from app.core.domain.value_objects import Currency, Money

            # Check unique phone
            existing = await uow.abonents.get_by_phone(data.phone)
            if existing:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=f"Abonent with phone {data.phone} already exists",
                )

            # Check unique account number
            if data.account_number:
                existing_account = await uow.abonents.get_by_account(data.account_number)
                if existing_account:
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT,
                        detail=f"Abonent with account {data.account_number} already exists",
                    )

            balance = Money(data.balance, Currency(data.currency))
            abonent = Abonent(
                full_name=data.full_name,
                phone=data.phone,
                account_number=data.account_number,
                balance=balance,
                allow_negative=data.allow_negative,
                tariff_id=data.tariff_id,
            )
            saved = await uow.abonents.save(abonent)
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
    ) -> AbonentResponse:
        """Обновить абонента частично (PATCH)."""
        async with uow:
            abonent = await uow.abonents.get(abonent_id)
            if not abonent:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Abonent with id {abonent_id} not found",
                )

            # Apply changes
            if data.full_name is not None:
                abonent._full_name = data.full_name
            if data.phone is not None:
                existing = await uow.abonents.get_by_phone(data.phone)
                if existing and existing.id != abonent_id:
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT,
                        detail=f"Phone {data.phone} already belongs to another abonent",
                    )
                abonent._phone = data.phone
            if data.status is not None:
                from app.core.domain.value_objects import AbonentStatus
                abonent._status = AbonentStatus(data.status)
            if data.tariff_id is not None:
                abonent.assign_tariff(data.tariff_id)
            if data.allow_negative is not None:
                abonent._allow_negative = data.allow_negative

            saved = await uow.abonents.save(abonent)
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
    ) -> None:
        """Удалить абонента (изменить статус на INACTIVE)."""
        async with uow:
            abonent = await uow.abonents.get(abonent_id)
            if not abonent:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Abonent with id {abonent_id} not found",
                )
            abonent._status = AbonentStatus.INACTIVE
            await uow.abonents.save(abonent)
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
    ) -> AbonentResponse:
        """Пополнить баланс абонента на указанную сумму."""
        async with uow:
            from app.core.domain.value_objects import Money

            abonent = await uow.abonents.get(abonent_id)
            if not abonent:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Abonent with id {abonent_id} not found",
                )
            abonent.change_balance(Money(float(data.amount), "RUB"), reason="Manual top-up")
            saved = await uow.abonents.save(abonent)
            await uow.commit()
            return AbonentResponse.model_validate(saved, from_attributes=True)
