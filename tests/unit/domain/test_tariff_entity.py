# =============================================================================
# shm-next — Tariff Entity Tests
# =============================================================================
"""Тесты для сущности Tariff."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.entities.tariff import Tariff


class TestTariffCreation:
    """Тесты создания тарифа."""

    def test_create_minimal(self):
        """Создание с минимальными параметрами."""
        tariff = Tariff(name="Basic")

        assert tariff.id is not None
        assert tariff.name == "Basic"
        assert tariff.description == ""
        assert tariff.is_active is True
        assert tariff.price == 0
        assert tariff.currency == "RUB"
        assert tariff.billing_period == "monthly"
        assert tariff.version == 1
        assert tariff.services == []

    def test_create_full(self):
        """Создание со всеми параметрами."""
        tariff = Tariff(
            name="Premium",
            description="Premium plan with all features",
            services=[{"type": "voice", "cost": 500}],
            is_active=True,
            price=1500,
            currency="RUB",
            billing_period="monthly",
        )

        assert tariff.name == "Premium"
        assert tariff.description == "Premium plan with all features"
        assert tariff.services == [{"type": "voice", "cost": 500}]
        assert tariff.is_active is True
        assert tariff.price == 1500
        assert tariff.currency == "RUB"
        assert tariff.billing_period == "monthly"

    def test_custom_id(self):
        """Создание с указанным ID."""
        custom_id = uuid4()
        tariff = Tariff(id=custom_id, name="Custom")

        assert tariff.id == custom_id

    def test_default_services_empty(self):
        """Список услуг по умолчанию пуст."""
        tariff = Tariff(name="Free")

        assert tariff.services == []


class TestTariffProperties:
    """Тесты свойств тарифа."""

    def test_name_setter(self):
        tariff = Tariff(name="Old Name")
        tariff.name = "New Name"

        assert tariff.name == "New Name"

    def test_description_setter(self):
        tariff = Tariff(description="Old")
        tariff.description = "New"

        assert tariff.description == "New"

    def test_is_active_setter(self):
        tariff = Tariff(name="Test", is_active=True)
        tariff.is_active = False

        assert tariff.is_active is False
        assert tariff.version == 2

    def test_services_setter(self):
        tariff = Tariff(name="Test")
        tariff.services = [{"type": "data", "cost": 100}]

        assert tariff.services == [{"type": "data", "cost": 100}]

    def test_price_and_currency(self):
        tariff = Tariff(name="Test", price=999, currency="USD")

        assert tariff.price == 999
        assert tariff.currency == "USD"

    def test_billing_period(self):
        tariff = Tariff(name="Test", billing_period="daily")

        assert tariff.billing_period == "daily"


class TestTariffVersioning:
    """Тесты версионирования тарифа."""

    def test_version_increments_on_is_active_change(self):
        tariff = Tariff(name="Test", is_active=True)
        assert tariff.version == 1

        tariff.is_active = False
        assert tariff.version == 2

        tariff.is_active = True
        assert tariff.version == 3

    def test_version_preserved_on_creation(self):
        tariff = Tariff(name="Test", version=10)

        assert tariff.version == 10

    def test_other_setters_do_not_increment_version(self):
        """Сеттеры name/description/services не меняют version."""
        tariff = Tariff(name="Test", version=5)

        tariff.name = "Updated"
        assert tariff.version == 5

        tariff.description = "Updated desc"
        assert tariff.version == 5

        tariff.services = [{"type": "voice"}]
        assert tariff.version == 5


class TestTariffTimestamps:
    """Тесты временных меток."""

    def test_created_at_set_on_creation(self):
        tariff = Tariff(name="Test")

        assert tariff.created_at is not None

    def test_updated_at_changes_on_is_active_change(self):
        tariff = Tariff(name="Test", is_active=True)
        old_updated = tariff.updated_at

        tariff.is_active = False

        assert tariff.updated_at > old_updated
