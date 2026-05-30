# =============================================================================
# shm-next — ServiceService Tests
# =============================================================================
"""Тесты для ServiceService (application layer)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.application.services.service_service import ServiceService
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.catalog_service import CatalogService
from app.core.domain.entities.service import ServiceStatus, UserService
from app.core.domain.value_objects import AbonentStatus, Money


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


class TestServiceServiceSHMCompatibility:
    """Тесты SHM-сценариев заказа, продления и удаления услуг."""

    def setup_method(self):
        self.service_repo = AsyncMock()
        self.catalog_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = ServiceService(
            service_repo=self.service_repo,
            event_bus=self.event_bus,
            catalog_service_repo=self.catalog_repo,
        )

    @pytest.mark.asyncio
    async def test_order_catalog_service_charges_balance_and_sets_expire_at(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        starts_at = datetime(2026, 5, 27, tzinfo=UTC)
        catalog = CatalogService(
            id=catalog_id,
            name="Internet 100M",
            category="internet",
            cost=Money("500.00"),
            period_cost="1.0000",
        )
        abonent = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000010",
            balance=Money("1000.00"),
            status=AbonentStatus.ACTIVE,
        )
        self.catalog_repo.get.return_value = catalog
        self.service_repo.get_abonent.return_value = abonent
        self.service_repo.save.side_effect = lambda service: service
        self.service_repo.save_abonent.side_effect = lambda abonent: abonent

        result = await self.service.order_catalog_service(
            abonent_id=abonent_id,
            catalog_service_id=catalog_id,
            quantity=1,
            now=starts_at,
        )

        assert result.status == ServiceStatus.ACTIVE
        assert result.catalog_service_id == catalog_id
        assert result.expire_at == starts_at + timedelta(days=30)
        assert result.cost == 500.0
        assert abonent.balance == Money("500.00")
        self.service_repo.save_abonent.assert_called_once()
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_order_catalog_service_rejects_insufficient_balance(self):
        catalog_id = uuid4()
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Internet 100M",
            cost=Money("500.00"),
        )
        self.service_repo.get_abonent.return_value = Abonent(
            id=uuid4(),
            full_name="Poor",
            phone="+79990000011",
            balance=Money("100.00"),
            status=AbonentStatus.ACTIVE,
        )

        with pytest.raises(ValueError, match="Insufficient balance"):
            await self.service.order_catalog_service(
                abonent_id=uuid4(),
                catalog_service_id=catalog_id,
            )

        self.service_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_order_catalog_service_rejects_quantity_above_max_count(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Static IP",
            cost=Money("100.00"),
            max_count=1,
        )

        with pytest.raises(ValueError, match="max_count"):
            await self.service.order_catalog_service(
                abonent_id=abonent_id,
                catalog_service_id=catalog_id,
                quantity=2,
            )

        self.service_repo.get_abonent.assert_not_called()
        self.service_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_order_catalog_service_rejects_existing_active_above_max_count(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Static IP",
            cost=Money("100.00"),
            max_count=1,
        )
        self.service_repo.get_by_abonent.return_value = [
            UserService(
                abonent_id=abonent_id,
                service_type="ip",
                catalog_service_id=catalog_id,
                status=ServiceStatus.ACTIVE,
            )
        ]

        with pytest.raises(ValueError, match="max_count"):
            await self.service.order_catalog_service(
                abonent_id=abonent_id,
                catalog_service_id=catalog_id,
            )

        self.service_repo.get_by_abonent.assert_called_once_with(
            abonent_id=abonent_id,
            active_only=True,
        )
        self.service_repo.get_abonent.assert_not_called()
        self.service_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_renew_catalog_service_extends_from_existing_expire_at(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        service_id = uuid4()
        starts_at = datetime(2026, 5, 1, tzinfo=UTC)
        expire_at = datetime(2026, 5, 31, tzinfo=UTC)
        user_service = UserService(
            id=service_id,
            abonent_id=abonent_id,
            service_type="internet",
            catalog_service_id=catalog_id,
            status=ServiceStatus.ACTIVE,
            activated_at=starts_at,
            expire_at=expire_at,
            cost=500.0,
            period_cost="1.0000",
        )
        self.service_repo.get.return_value = user_service
        self.service_repo.get_abonent.return_value = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000012",
            balance=Money("1000.00"),
            status=AbonentStatus.ACTIVE,
        )
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Internet 100M",
            cost=Money("500.00"),
            period_cost="1.0000",
        )
        self.service_repo.save.side_effect = lambda service: service
        self.service_repo.save_abonent.side_effect = lambda abonent: abonent

        result = await self.service.renew_catalog_service(
            service_id=service_id,
            now=datetime(2026, 5, 20, tzinfo=UTC),
        )

        assert result.expire_at == expire_at + timedelta(days=30)
        assert result.status == ServiceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_renew_catalog_service_respects_no_discount(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        service_id = uuid4()
        user_service = UserService(
            id=service_id,
            abonent_id=abonent_id,
            service_type="internet",
            catalog_service_id=catalog_id,
            status=ServiceStatus.ACTIVE,
            activated_at=datetime(2026, 5, 1, tzinfo=UTC),
            expire_at=datetime(2026, 5, 31, tzinfo=UTC),
            cost=500.0,
            period_cost="1.0000",
            no_discount=True,
        )
        abonent = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000014",
            balance=Money("1000.00"),
            status=AbonentStatus.ACTIVE,
        )
        self.service_repo.get.return_value = user_service
        self.service_repo.get_abonent.return_value = abonent
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Internet 100M",
            cost=Money("500.00"),
            no_discount=True,
        )
        self.service_repo.save.side_effect = lambda service: service
        self.service_repo.save_abonent.side_effect = lambda abonent: abonent

        result = await self.service.renew_catalog_service(
            service_id=service_id,
            now=datetime(2026, 5, 20, tzinfo=UTC),
            abonent_discount_percent=50,
        )

        assert result.cost == 500.0
        assert abonent.balance == Money("500.00")

    @pytest.mark.asyncio
    async def test_renew_due_catalog_services_renews_expired_auto_bill_services(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        service_id = uuid4()
        now = datetime(2026, 6, 1, tzinfo=UTC)
        due_service = UserService(
            id=service_id,
            abonent_id=abonent_id,
            service_type="internet",
            catalog_service_id=catalog_id,
            status=ServiceStatus.ACTIVE,
            activated_at=datetime(2026, 5, 1, tzinfo=UTC),
            expire_at=now,
            cost=500.0,
            period_cost="1.0000",
            auto_bill=True,
        )
        abonent = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000015",
            balance=Money("1000.00"),
            status=AbonentStatus.ACTIVE,
        )
        self.service_repo.get_expiring_auto_bill.return_value = [due_service]
        self.service_repo.get.return_value = due_service
        self.service_repo.get_abonent.return_value = abonent
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Internet 100M",
            cost=Money("500.00"),
            period_cost="1.0000",
        )
        self.service_repo.save.side_effect = lambda service: service
        self.service_repo.save_abonent.side_effect = lambda abonent: abonent

        result = await self.service.renew_due_catalog_services(now=now, limit=50)

        assert result["processed"] == 1
        assert result["renewed"] == 1
        assert result["suspended"] == 0
        assert result["failed"] == 0
        assert result["errors"] == []
        assert due_service.expire_at == now + timedelta(days=30)
        assert abonent.balance == Money("500.00")
        self.service_repo.get_expiring_auto_bill.assert_called_once_with(
            cutoff=now,
            limit=50,
        )

    @pytest.mark.asyncio
    async def test_renew_due_catalog_services_counts_suspended_on_insufficient_balance(self):
        abonent_id = uuid4()
        catalog_id = uuid4()
        service_id = uuid4()
        now = datetime(2026, 6, 1, tzinfo=UTC)
        due_service = UserService(
            id=service_id,
            abonent_id=abonent_id,
            service_type="internet",
            catalog_service_id=catalog_id,
            status=ServiceStatus.ACTIVE,
            activated_at=datetime(2026, 5, 1, tzinfo=UTC),
            expire_at=now,
            cost=500.0,
            period_cost="1.0000",
            auto_bill=True,
        )
        self.service_repo.get_expiring_auto_bill.return_value = [due_service]
        self.service_repo.get.return_value = due_service
        self.service_repo.get_abonent.return_value = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000016",
            balance=Money("100.00"),
            status=AbonentStatus.ACTIVE,
        )
        self.catalog_repo.get.return_value = CatalogService(
            id=catalog_id,
            name="Internet 100M",
            cost=Money("500.00"),
        )
        self.service_repo.save.side_effect = lambda service: service

        result = await self.service.renew_due_catalog_services(now=now)

        assert result["processed"] == 1
        assert result["renewed"] == 0
        assert result["suspended"] == 1
        assert result["failed"] == 0
        assert result["errors"][0]["service_id"] == str(service_id)
        assert due_service.status == ServiceStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_stop_catalog_service_refunds_unused_period(self):
        abonent_id = uuid4()
        service_id = uuid4()
        starts_at = datetime(2026, 5, 1, tzinfo=UTC)
        expire_at = datetime(2026, 5, 31, tzinfo=UTC)
        abonent = Abonent(
            id=abonent_id,
            full_name="Active",
            phone="+79990000013",
            balance=Money("0.00"),
            status=AbonentStatus.ACTIVE,
        )
        user_service = UserService(
            id=service_id,
            abonent_id=abonent_id,
            service_type="internet",
            status=ServiceStatus.ACTIVE,
            activated_at=starts_at,
            expire_at=expire_at,
            cost=300.0,
        )
        self.service_repo.get.return_value = user_service
        self.service_repo.get_abonent.return_value = abonent
        self.service_repo.save.side_effect = lambda service: service
        self.service_repo.save_abonent.side_effect = lambda abonent: abonent

        result = await self.service.stop_catalog_service(
            service_id=service_id,
            stopped_at=datetime(2026, 5, 16, tzinfo=UTC),
        )

        assert result.status == ServiceStatus.DEACTIVATED
        assert abonent.balance == Money("150.00")
