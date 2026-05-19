# =============================================================================
# shm-next — ServiceService Tests
# =============================================================================
"""Тесты для ServiceService (application layer)."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.application.services.service_service import ServiceService
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.service import ServiceStatus, UserService
from app.core.domain.value_objects import AbonentStatus


class TestServiceServiceBlockedAbonent:
    """Тесты ServiceService с заблокированными/неактивными абонентами."""

    def setup_method(self):
        self.service_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = ServiceService(
            service_repo=self.service_repo,
            event_bus=self.event_bus,
        )

    @pytest.mark.asyncio
    async def test_activate_service_blocked_abonent(self):
        """Нельзя подключить услугу заблокированному абоненту."""
        abonent_id = uuid4()
        blocked_abonent = Abonent(
            id=abonent_id,
            full_name="Blocked",
            phone="+79990000001",
            status=AbonentStatus.BLOCKED,
        )
        self.service_repo.get_abonent.return_value = blocked_abonent

        with pytest.raises(ValueError, match="status"):
            await self.service.activate_service(
                abonent_id=abonent_id,
                service_type="internet",
            )

        self.service_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_service_disabled_abonent(self):
        """Нельзя подключить услугу деактивированному абоненту."""
        abonent_id = uuid4()
        disabled_abonent = Abonent(
            id=abonent_id,
            full_name="Disabled",
            phone="+79990000002",
            status=AbonentStatus.DISABLED,
        )
        self.service_repo.get_abonent.return_value = disabled_abonent

        with pytest.raises(ValueError, match="status"):
            await self.service.activate_service(
                abonent_id=abonent_id,
                service_type="internet",
            )

        self.service_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_service_abonent_not_found(self):
        """Нельзя подключить услугу, если абонент не найден."""
        abonent_id = uuid4()
        self.service_repo.get_abonent.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await self.service.activate_service(
                abonent_id=abonent_id,
                service_type="internet",
            )

        self.service_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_service_active_abonent_succeeds(self):
        """Подключение услуги активному абоненту — успех."""
        abonent_id = uuid4()
        active_abonent = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000003",
            status=AbonentStatus.ACTIVE,
        )
        self.service_repo.get_abonent.return_value = active_abonent
        saved_service = UserService(
            abonent_id=abonent_id,
            service_type="internet",
            status=ServiceStatus.ACTIVE,
        )
        self.service_repo.save.return_value = saved_service

        result = await self.service.activate_service(
            abonent_id=abonent_id,
            service_type="internet",
        )

        assert result is not None
        assert result.status == ServiceStatus.ACTIVE
        self.service_repo.save.assert_called_once()
        self.event_bus.publish.assert_called_once()


class TestServiceService:
    """Тесты ServiceService."""

    def setup_method(self):
        self.service_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = ServiceService(
            service_repo=self.service_repo,
            event_bus=self.event_bus,
        )
        self.service_repo.get_abonent = AsyncMock()
        self.service_repo.get_abonent.return_value = Abonent(
            id=uuid4(),
            full_name="Active",
            phone="+79990000003",
            status=AbonentStatus.ACTIVE,
        )

    @pytest.mark.asyncio
    async def test_activate_service_success(self):
        """Подключение услуги — успех."""
        abonent_id = uuid4()
        saved_service = UserService(
            abonent_id=abonent_id,
            service_type="internet",
            status=ServiceStatus.ACTIVE,
        )
        self.service_repo.save.return_value = saved_service

        result = await self.service.activate_service(
            abonent_id=abonent_id,
            service_type="internet",
        )

        assert result is not None
        assert result.service_type == "internet"
        assert result.status == ServiceStatus.ACTIVE
        self.service_repo.save.assert_called_once()
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_service_with_tariff(self):
        """Подключение услуги с привязкой к тарифу."""
        abonent_id = uuid4()
        tariff_service_id = uuid4()
        saved_service = UserService(
            abonent_id=abonent_id,
            service_type="voice",
            tariff_service_id=tariff_service_id,
            status=ServiceStatus.ACTIVE,
        )
        self.service_repo.save.return_value = saved_service

        result = await self.service.activate_service(
            abonent_id=abonent_id,
            service_type="voice",
            tariff_service_id=tariff_service_id,
        )

        assert result.tariff_service_id == tariff_service_id

    @pytest.mark.asyncio
    async def test_activate_service_with_metadata(self):
        """Подключение услуги с метаданными."""
        abonent_id = uuid4()
        meta = {"source": "api"}
        saved_service = UserService(
            abonent_id=abonent_id,
            service_type="data",
            metadata=meta,
            status=ServiceStatus.ACTIVE,
        )
        self.service_repo.save.return_value = saved_service

        result = await self.service.activate_service(
            abonent_id=abonent_id,
            service_type="data",
            metadata=meta,
        )

        assert result.metadata == meta

    @pytest.mark.asyncio
    async def test_deactivate_service_success(self):
        """Отключение услуги — успех."""
        service_id = uuid4()
        abonent_id = uuid4()
        # Создаём активную услугу (через INIT -> activate)
        active_service = UserService(
            abonent_id=abonent_id,
            service_type="internet",
            status=ServiceStatus.INIT,
        )
        active_service.activate()
        self.service_repo.get.return_value = active_service
        self.service_repo.save.return_value = active_service

        result = await self.service.deactivate_service(
            service_id=service_id,
            reason="user_request",
        )

        assert result is not None
        assert result.status == ServiceStatus.DEACTIVATED
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_service_not_found(self):
        """Отключение услуги — не найдена."""
        self.service_repo.get.return_value = None

        result = await self.service.deactivate_service(uuid4())

        assert result is None
        self.event_bus.publish.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivate_service_without_reason(self):
        """Отключение услуги без указания причины."""
        service_id = uuid4()
        abonent_id = uuid4()
        # Создаём активную услугу через доменный метод
        active_service = UserService(
            abonent_id=abonent_id,
            service_type="sms",
            status=ServiceStatus.INIT,
        )
        active_service.activate()
        self.service_repo.get.return_value = active_service
        self.service_repo.save.return_value = active_service

        result = await self.service.deactivate_service(service_id=service_id)

        assert result is not None
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_services(self):
        """Получение списка услуг абонента."""
        abonent_id = uuid4()
        services = [
            UserService(abonent_id=abonent_id, service_type="internet", status=ServiceStatus.ACTIVE),
            UserService(abonent_id=abonent_id, service_type="voice", status=ServiceStatus.ACTIVE),
        ]
        self.service_repo.get_by_abonent.return_value = services

        result = await self.service.get_services(abonent_id)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_service_found(self):
        """Получение услуги по ID — найдена."""
        service_id = uuid4()
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
            status=ServiceStatus.ACTIVE,
        )
        self.service_repo.get.return_value = service

        result = await self.service.get_service(service_id)

        assert result is service

    @pytest.mark.asyncio
    async def test_get_service_not_found(self):
        """Получение услуги по ID — не найдена."""
        self.service_repo.get.return_value = None

        result = await self.service.get_service(uuid4())

        assert result is None
