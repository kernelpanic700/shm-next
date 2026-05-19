# =============================================================================
# shm-next — TariffService Tests
# =============================================================================
"""Тесты для TariffService (application layer)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.application.tariffs.tariff_service import TariffService
from app.core.domain.entities.tariff import Tariff


class TestTariffService:
    """Тесты TariffService."""

    def setup_method(self):
        self.tariff_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = TariffService(
            tariff_repo=self.tariff_repo,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_get_tariff_found(self):
        """Получение тарифа по ID — найден."""
        tariff_id = uuid4()
        tariff = Tariff(name="Basic", id=tariff_id)
        self.tariff_repo.get.return_value = tariff

        result = await self.service.get_tariff(tariff_id)

        assert result is tariff
        assert result.name == "Basic"

    @pytest.mark.asyncio
    async def test_get_tariff_not_found(self):
        """Получение тарифа по ID — не найден."""
        self.tariff_repo.get.return_value = None

        result = await self.service.get_tariff(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_tariff_by_name_found(self):
        """Получение тарифа по имени — найден."""
        tariff = Tariff(name="Premium")
        self.tariff_repo.get_by_name.return_value = tariff

        result = await self.service.get_tariff_by_name("Premium")

        assert result is tariff

    @pytest.mark.asyncio
    async def test_get_tariff_by_name_not_found(self):
        """Получение тарифа по имени — не найден."""
        self.tariff_repo.get_by_name.return_value = None

        result = await self.service.get_tariff_by_name("NonExistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_tariffs_active_only(self):
        """Список тарифов — только активные."""
        tariffs = [
            Tariff(name="Basic", is_active=True),
            Tariff(name="Premium", is_active=True),
        ]
        self.tariff_repo.list.return_value = tariffs

        result = await self.service.list_tariffs(active_only=True)

        assert len(result) == 2
        self.tariff_repo.list.assert_called_once_with(active_only=True)

    @pytest.mark.asyncio
    async def test_list_tariffs_all(self):
        """Список тарифов — все."""
        tariffs = [
            Tariff(name="Basic", is_active=True),
            Tariff(name="Premium", is_active=False),
        ]
        self.tariff_repo.list.return_value = tariffs

        result = await self.service.list_tariffs(active_only=False)

        assert len(result) == 2
        self.tariff_repo.list.assert_called_once_with(active_only=False)

    @pytest.mark.asyncio
    async def test_create_tariff(self):
        """Создание тарифа."""
        data = MagicMock()
        data.name = "New Tariff"
        data.description = "Test tariff"
        data.services = []
        data.is_active = True

        created_tariff = Tariff(name="New Tariff", description="Test tariff", services=[], is_active=True)
        self.tariff_repo.save.return_value = created_tariff

        result = await self.service.create_tariff(data)

        assert result.name == "New Tariff"
        assert result.description == "Test tariff"
        self.tariff_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tariff_found(self):
        """Обновление тарифа — найден."""
        tariff_id = uuid4()
        existing_tariff = Tariff(name="Existing", id=tariff_id)
        updated_tariff = Tariff(name="Updated", id=tariff_id)

        self.tariff_repo.get.return_value = existing_tariff
        self.tariff_repo.save.return_value = updated_tariff

        data = MagicMock()
        data.model_dump.return_value = {"name": "Updated"}

        result = await self.service.update_tariff(tariff_id, data)

        assert result.name == "Updated"
        self.tariff_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tariff_not_found(self):
        """Обновление тарифа — не найден."""
        tariff_id = uuid4()
        self.tariff_repo.get.return_value = None

        data = MagicMock()

        with pytest.raises(ValueError, match="not found"):
            await self.service.update_tariff(tariff_id, data)

        self.tariff_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_tariff_services(self):
        """Получение услуг тарифа."""
        tariff_id = uuid4()
        services = [
            {"id": uuid4(), "service_type": "voice", "name": "Voice", "cost": 500.0, "currency": "RUB", "unit": "month", "is_optional": False},
        ]
        self.tariff_repo.get_services_for_tariff.return_value = services

        result = await self.service.get_tariff_services(tariff_id)

        assert len(result) == 1
        assert result[0]["service_type"] == "voice"
