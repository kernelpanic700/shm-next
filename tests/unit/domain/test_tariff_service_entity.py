# =============================================================================
# shm-next — Unit Tests: TariffService Entity
# =============================================================================
"""Тесты для TariffService."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.entities.tariff_service import TariffService
from app.core.domain.value_objects import Money


class TestTariffService:
    """Тесты TariffService."""

    def test_create_default(self):
        ts = TariffService()
        assert ts.id is not None
        assert ts.service_type == ""
        assert ts.cost is None
        assert ts.billing_period == "monthly"
        assert ts.is_optional is False
        assert ts.sort_order == 0

    def test_create_with_params(self):
        ts_id = uuid4()
        tariff_id = uuid4()
        ts = TariffService(
            id=ts_id,
            tariff_id=tariff_id,
            service_type="voice",
            cost=Money(100, "RUB"),
            billing_period="monthly",
            is_optional=True,
            sort_order=5,
        )
        assert ts.id == ts_id
        assert ts.tariff_id == tariff_id
        assert ts.service_type == "voice"
        assert ts.cost.amount == 100
        assert ts.billing_period == "monthly"
        assert ts.is_optional is True
        assert ts.sort_order == 5

    def test_update_cost(self):
        ts = TariffService(cost=Money(100, "RUB"))
        initial_version = ts.version
        ts.update_cost(Money(150, "RUB"))
        assert ts.cost.amount == 150
        assert ts.version == initial_version + 1

    def test_set_sort_order(self):
        ts = TariffService(sort_order=1)
        initial_version = ts.version
        ts.set_sort_order(10)
        assert ts.sort_order == 10
        assert ts.version == initial_version + 1
