# =============================================================================
# shm-next — ProcessBillingService Tests
# =============================================================================
"""Тесты для ProcessBillingService (application layer)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.application.billing.process_billing import ProcessBillingService
from app.core.services.billing_engine import BillingEngine


class TestProcessBillingService:
    """Тесты ProcessBillingService."""

    def setup_method(self):
        self.abonent_repo = AsyncMock()
        self.service_repo = AsyncMock()
        self.billing_engine = MagicMock(spec=BillingEngine)
        self.event_bus = AsyncMock()
        self.action_registry = MagicMock()
        self.service = ProcessBillingService(
            abonent_repo=self.abonent_repo,
            service_repo=self.service_repo,
            billing_engine=self.billing_engine,
            event_bus=self.event_bus,
            action_registry=self.action_registry,
        )

    @pytest.mark.asyncio
    async def test_process_single_no_services(self):
        """Обработка абонента без активных услуг."""
        self.service_repo.get_by_abonent.return_value = []

        result = await self.service.process_single(uuid4())

        assert result["success"] is True
        assert result["message"] == "No active services"

    @pytest.mark.asyncio
    async def test_process_single_with_services(self):
        """Обработка абонента с активными услугами."""
        service_id = uuid4()
        mock_service = MagicMock()
        mock_service.id = service_id
        mock_service.cost = 3000.0
        mock_service.currency = "RUB"
        mock_service.activated_at = None  # Will use date.today()

        self.service_repo.get_by_abonent.return_value = [mock_service]

        # Mock the billing engine to return a known amount
        from app.core.domain.value_objects import Money
        self.billing_engine.calculate_withdraw.return_value = Money(100.0, "RUB")

        result = await self.service.process_single(uuid4())

        assert result["success"] is True
        assert result["services_count"] == 1
        assert isinstance(result["amount"], float)
        assert result["currency"] == "RUB"

    @pytest.mark.asyncio
    async def test_process_single_multiple_services(self):
        """Обработка абонента с несколькими услугами."""
        mock_service1 = MagicMock()
        mock_service1.id = uuid4()
        mock_service1.cost = 1000.0
        mock_service1.currency = "RUB"
        mock_service1.activated_at = None

        mock_service2 = MagicMock()
        mock_service2.id = uuid4()
        mock_service2.cost = 2000.0
        mock_service2.currency = "RUB"
        mock_service2.activated_at = None

        self.service_repo.get_by_abonent.return_value = [mock_service1, mock_service2]

        from app.core.domain.value_objects import Money
        self.billing_engine.calculate_withdraw.return_value = Money(50.0, "RUB")

        result = await self.service.process_single(uuid4())

        assert result["success"] is True
        assert result["services_count"] == 2
        # 2 services * 50.0 = 100.0
        assert result["amount"] == 100.0

    @pytest.mark.asyncio
    async def test_process_all_expired_empty(self):
        """Обработка всех абонентов — пустой список."""
        self.abonent_repo.list.return_value = []

        result = await self.service.process_all_expired(batch_size=100)

        assert result["total_processed"] == 0
        assert result["successful_withdraws"] == 0
        assert result["failed_withdraws"] == 0
        assert result["total_amount"] == 0.0

    @pytest.mark.asyncio
    async def test_process_all_expired_with_abonents(self):
        """Обработка всех абонентов — с данными."""
        abonent1 = MagicMock()
        abonent1.id = uuid4()
        abonent2 = MagicMock()
        abonent2.id = uuid4()

        self.abonent_repo.list.return_value = [abonent1, abonent2]

        # process_single returns success
        self.service_repo.get_by_abonent.return_value = []

        result = await self.service.process_all_expired(batch_size=100)

        assert result["total_processed"] == 2
        assert result["successful_withdraws"] == 2

    @pytest.mark.asyncio
    async def test_process_all_expired_with_error(self):
        """Обработка всех абонентов — ошибка при обработке одного."""
        abonent1 = MagicMock()
        abonent1.id = uuid4()

        self.abonent_repo.list.return_value = [abonent1]

        # Force an exception in process_single
        self.service_repo.get_by_abonent.side_effect = Exception("DB error")

        result = await self.service.process_all_expired(batch_size=100)

        assert result["total_processed"] == 0
        assert result["failed_withdraws"] == 1
