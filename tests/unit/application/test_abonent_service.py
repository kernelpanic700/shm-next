# =============================================================================
# shm-next — Unit Tests: AbonentService
# =============================================================================
"""Тесты для AbonentService."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.application.abonents.abonent_service import AbonentService
from app.core.domain.entities.abonent import Abonent, AbonentCreate, AbonentUpdate
from app.core.domain.value_objects import Money


class TestAbonentService:
    """Тесты AbonentService."""

    def setup_method(self):
        self.repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = AbonentService(
            abonent_repo=self.repo,
            event_bus=self.event_bus,
        )

    def test_init(self):
        assert self.service._abonent_repo is self.repo
        assert self.service._event_bus is self.event_bus

    @pytest.mark.asyncio
    async def test_create_abonent_success(self):
        data = AbonentCreate(
            full_name="Тест Абонент",
            phone="+79991234567",
            account_number="ACC001",
            balance=1000.0,
        )
        self.repo.get_by_phone.return_value = None
        self.repo.get_by_account.return_value = None
        saved_abonent = Abonent(
            full_name=data.full_name,
            phone=data.phone,
            account_number=data.account_number,
            balance=Money(data.balance, "RUB"),
        )
        self.repo.save.return_value = saved_abonent

        result = await self.service.create_abonent(data)

        assert result.full_name == "Тест Абонент"
        assert result.phone == "+79991234567"
        self.repo.get_by_phone.assert_called_once_with("+79991234567")
        self.repo.get_by_account.assert_called_once_with("ACC001")
        self.repo.save.assert_called_once()
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_abonent_duplicate_phone(self):
        data = AbonentCreate(
            full_name="Тест Абонент",
            phone="+79991234567",
            account_number="ACC001",
        )
        self.repo.get_by_phone.return_value = Abonent(phone="+79991234567")

        with pytest.raises(ValueError, match="already exists"):
            await self.service.create_abonent(data)

        self.repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_abonent_duplicate_account(self):
        data = AbonentCreate(
            full_name="Тест",
            phone="+79990000000",
            account_number="ACC001",
        )
        self.repo.get_by_phone.return_value = None
        self.repo.get_by_account.return_value = Abonent(account_number="ACC001")

        with pytest.raises(ValueError, match="already exists"):
            await self.service.create_abonent(data)

        self.repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_abonent_found(self):
        abonent_id = uuid4()
        abonent = Abonent(id=abonent_id, full_name="Тест")
        self.repo.get.return_value = abonent

        result = await self.service.get_abonent(abonent_id)

        assert result is abonent
        self.repo.get.assert_called_once_with(abonent_id)

    @pytest.mark.asyncio
    async def test_get_abonent_not_found(self):
        abonent_id = uuid4()
        self.repo.get.return_value = None

        result = await self.service.get_abonent(abonent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_abonents(self):
        abonents = [
            Abonent(full_name="Абонент 1", phone="+79990000001"),
            Abonent(full_name="Абонент 2", phone="+79990000002"),
        ]
        self.repo.list.return_value = abonents

        result = await self.service.list_abonents(offset=0, limit=10)

        assert len(result) == 2
        self.repo.list.assert_called_once_with(offset=0, limit=10, status=None)

    @pytest.mark.asyncio
    async def test_update_abonent_found(self):
        abonent_id = uuid4()
        abonent = Abonent(id=abonent_id, full_name="Старое имя")
        data = AbonentUpdate(full_name="Новое имя")
        self.repo.get.return_value = abonent
        self.repo.save.return_value = abonent

        result = await self.service.update_abonent(abonent_id, data)

        assert result is abonent
        assert result.full_name == "Новое имя"

    @pytest.mark.asyncio
    async def test_update_abonent_not_found(self):
        abonent_id = uuid4()
        self.repo.get.return_value = None
        data = AbonentUpdate(full_name="Новое имя")

        result = await self.service.update_abonent(abonent_id, data)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_abonent(self):
        abonent_id = uuid4()
        self.repo.delete.return_value = True

        result = await self.service.delete_abonent(abonent_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_change_balance(self):
        abonent_id = uuid4()
        abonent = Abonent(id=abonent_id, balance=Money(1000, "RUB"))
        self.repo.get.return_value = abonent
        self.repo.save.return_value = abonent

        result = await self.service.change_balance(
            abonent_id, amount=500, currency="RUB", reason="Пополнение"
        )

        assert result.balance.amount == 1500
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_balance_insufficient(self):
        abonent_id = uuid4()
        abonent = Abonent(id=abonent_id, balance=Money(100, "RUB"), allow_negative=False)
        self.repo.get.return_value = abonent

        with pytest.raises(ValueError, match="cannot be negative"):
            await self.service.change_balance(
                abonent_id, amount=-500, currency="RUB", reason="Test"
            )
