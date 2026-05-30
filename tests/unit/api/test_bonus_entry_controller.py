from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from litestar.exceptions import HTTPException

from app.api.dto.requests import BonusEntryCreateRequest
from app.api.v1.bonus_entries import BonusEntryController
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.bonus_entry import BonusEntry
from app.core.domain.value_objects import Money


class FakeAbonentRepo:
    def __init__(self, abonent: Abonent | None) -> None:
        self.abonent = abonent

    async def get(self, abonent_id):
        return self.abonent if self.abonent and self.abonent.id == abonent_id else None


class FakeBonusRepo:
    def __init__(self, entries: list[BonusEntry] | None = None) -> None:
        self.entries = entries or []
        self.saved: list[BonusEntry] = []

    async def get(self, entry_id):
        return next((entry for entry in self.entries if entry.id == entry_id), None)

    async def get_by_abonent(self, abonent_id):
        return [entry for entry in self.entries if entry.abonent_id == abonent_id]

    async def get_active(self):
        return [entry for entry in self.entries if entry.is_active]

    async def get_expired(self):
        return [entry for entry in self.entries if entry.is_expired()]

    async def save(self, entry):
        self.saved.append(entry)
        if entry not in self.entries:
            self.entries.append(entry)
        return entry


class FakeUnitOfWork:
    def __init__(self, abonent: Abonent | None, entries: list[BonusEntry] | None = None) -> None:
        self.abonents = FakeAbonentRepo(abonent)
        self.bonus_entries = FakeBonusRepo(entries)
        self.commit_count = 0

    async def commit(self):
        self.commit_count += 1


@pytest.mark.asyncio
async def test_create_bonus_entry() -> None:
    abonent = Abonent(id=uuid4(), full_name="Test")
    uow = FakeUnitOfWork(abonent)

    response = await BonusEntryController.create_bonus_entry.fn(
        None,
        data=BonusEntryCreateRequest(
            abonent_id=abonent.id,
            amount=Decimal("50.00"),
            reason="promo",
            expires_at=datetime.now(UTC) + timedelta(days=5),
        ),
        uow=uow,
    )

    assert response.abonent_id == abonent.id
    assert response.amount == 50.0
    assert response.reason == "promo"
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_create_bonus_entry_returns_404_for_missing_abonent() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await BonusEntryController.create_bonus_entry.fn(
            None,
            data=BonusEntryCreateRequest(
                abonent_id=uuid4(),
                amount=Decimal("10.00"),
            ),
            uow=FakeUnitOfWork(None),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_bonus_entries_by_abonent() -> None:
    abonent = Abonent(id=uuid4(), full_name="Test")
    entry = BonusEntry(abonent_id=abonent.id, amount=Money("10.00"))
    uow = FakeUnitOfWork(abonent, [entry])

    response = await BonusEntryController.list_bonus_entries.fn(
        None,
        uow=uow,
        abonent_id=abonent.id,
    )

    assert response.total == 1
    assert response.items[0].id == entry.id


@pytest.mark.asyncio
async def test_expire_bonus_entry() -> None:
    abonent = Abonent(id=uuid4(), full_name="Test")
    entry = BonusEntry(abonent_id=abonent.id, amount=Money("10.00"))
    uow = FakeUnitOfWork(abonent, [entry])

    response = await BonusEntryController.expire_bonus_entry.fn(
        None,
        entry_id=entry.id,
        uow=uow,
    )

    assert response.is_active is False
    assert uow.commit_count == 1
