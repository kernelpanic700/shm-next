# =============================================================================
# shm-next - API v1: Bonus Entries
# =============================================================================
from __future__ import annotations

from uuid import UUID

from litestar import Controller, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.api.dependencies import provide_uow_dependency
from app.api.dto.requests import BonusEntryCreateRequest
from app.api.dto.responses import BonusEntryListResponse, BonusEntryResponse
from app.core.domain.entities.bonus_entry import BonusEntry
from app.core.domain.value_objects import Money
from app.infrastructure.db.unit_of_work import UnitOfWork


class BonusEntryController(Controller):
    """Контроллер бонусных записей абонентов."""

    path = "/bonus-entries"
    tags = ["Bonus Entries"]
    dependencies = {"uow": Provide(provide_uow_dependency)}

    @get("/", summary="Список бонусных записей")
    async def list_bonus_entries(
        self,
        uow: UnitOfWork,
        abonent_id: UUID | None = None,
        active_only: bool = False,
        expired_only: bool = False,
    ) -> BonusEntryListResponse:
        if abonent_id is not None:
            entries = await uow.bonus_entries.get_by_abonent(abonent_id)
            if active_only:
                entries = [entry for entry in entries if entry.can_use()]
            if expired_only:
                entries = [entry for entry in entries if entry.is_expired()]
        elif expired_only:
            entries = await uow.bonus_entries.get_expired()
        elif active_only:
            entries = await uow.bonus_entries.get_active()
        else:
            entries = await uow.bonus_entries.get_active()

        return BonusEntryListResponse(
            items=[BonusEntryResponse.model_validate(entry) for entry in entries],
            total=len(entries),
        )

    @get("/{entry_id:uuid}", summary="Получить бонусную запись")
    async def get_bonus_entry(
        self,
        entry_id: UUID,
        uow: UnitOfWork,
    ) -> BonusEntryResponse:
        entry = await uow.bonus_entries.get(entry_id)
        if entry is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Bonus entry {entry_id} not found",
            )
        return BonusEntryResponse.model_validate(entry)

    @post("/", summary="Начислить бонус", status_code=HTTP_201_CREATED)
    async def create_bonus_entry(
        self,
        data: BonusEntryCreateRequest,
        uow: UnitOfWork,
    ) -> BonusEntryResponse:
        abonent = await uow.abonents.get(data.abonent_id)
        if abonent is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Abonent {data.abonent_id} not found",
            )

        entry = BonusEntry(
            abonent_id=data.abonent_id,
            amount=Money(data.amount, data.currency),
            reason=data.reason,
            expires_at=data.expires_at,
            source=data.source,
        )
        saved = await uow.bonus_entries.save(entry)
        await uow.commit()
        return BonusEntryResponse.model_validate(saved)

    @post("/{entry_id:uuid}/expire", summary="Деактивировать бонус")
    async def expire_bonus_entry(
        self,
        entry_id: UUID,
        uow: UnitOfWork,
    ) -> BonusEntryResponse:
        entry = await uow.bonus_entries.get(entry_id)
        if entry is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Bonus entry {entry_id} not found",
            )

        entry.expire()
        saved = await uow.bonus_entries.save(entry)
        await uow.commit()
        return BonusEntryResponse.model_validate(saved)
