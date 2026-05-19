# =============================================================================
# shm-next — UserService Entity Tests
# =============================================================================
"""Тесты для сущности UserService."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.domain.entities.service import ServiceStatus, UserService


class TestUserServiceCreation:
    """Тесты создания услуги абонента."""

    def test_create_minimal(self):
        """Создание с минимальными параметрами."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )

        assert service.id is not None
        assert service.abonent_id is not None
        assert service.service_type == "internet"
        assert service.status == ServiceStatus.INIT
        assert service.cost == 0
        assert service.currency == "RUB"
        assert service.version == 1

    def test_create_with_tariff_service(self):
        """Создание с привязкой к услуге тарифа."""
        tariff_service_id = uuid4()
        service = UserService(
            abonent_id=uuid4(),
            service_type="voice",
            tariff_service_id=tariff_service_id,
            cost=100.0,
            currency="RUB",
        )

        assert service.tariff_service_id == tariff_service_id
        assert service.cost == 100.0
        assert service.currency == "RUB"

    def test_create_with_metadata(self):
        """Создание с метаданными."""
        meta = {"source": "api", "plan": "premium"}
        service = UserService(
            abonent_id=uuid4(),
            service_type="data",
            metadata=meta,
        )

        assert service.metadata == meta

    def test_custom_id(self):
        """Создание с указанным ID."""
        custom_id = uuid4()
        service = UserService(
            id=custom_id,
            abonent_id=uuid4(),
            service_type="sms",
        )

        assert service.id == custom_id


class TestUserServiceActivation:
    """Тесты активации услуги."""

    def test_activate_from_init(self):
        """Активация из состояния INIT."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )

        assert service.status == ServiceStatus.INIT

        service.activate()

        assert service.status == ServiceStatus.ACTIVE
        assert service.activated_at is not None
        assert service.updated_at is not None
        assert service.version == 2

    def test_activate_sets_timestamps(self):
        """Активация устанавливает корректные временные метки."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="voice",
        )

        before = datetime.now(timezone.utc)
        service.activate()
        after = datetime.now(timezone.utc)

        assert before <= service.activated_at <= after
        assert before <= service.updated_at <= after


class TestUserServiceDeactivation:
    """Тесты деактивации услуги."""

    def test_deactivate(self):
        """Деактивация услуги."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )
        service.activate()

        service.deactivate(reason="user_request")

        assert service.status == ServiceStatus.DEACTIVATED
        assert service.deactivated_at is not None
        assert service.metadata.get("deactivation_reason") == "user_request"
        assert service.version == 3

    def test_deactivate_without_reason(self):
        """Деактивация без указания причины."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="sms",
        )
        service.activate()

        service.deactivate()

        assert service.status == ServiceStatus.DEACTIVATED
        assert service.metadata.get("deactivation_reason") is None



class TestUserServiceInvariants:
    """Тесты инвариантов UserService."""

    def test_cannot_activate_terminal_service(self):
        """Нельзя активировать услугу в терминальном состоянии DEACTIVATED."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )
        service.activate()
        service.deactivate(reason="user_request")

        with pytest.raises(ValueError, match="terminal"):
            service.activate()

    def test_cannot_deactivate_terminal_service(self):
        """Нельзя деактивировать услугу, которая уже DEACTIVATED."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="voice",
        )
        service.activate()
        service.deactivate(reason="user_request")

        with pytest.raises(ValueError, match="terminal"):
            service.deactivate()

    def test_cannot_activate_already_active(self):
        """Нельзя активировать уже активную услугу."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )
        service.activate()

        with pytest.raises(ValueError, match="already active"):
            service.activate()

    def test_activate_from_init_is_valid(self):
        """Активация из INIT — валидна."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )
        assert service.status == ServiceStatus.INIT

        service.activate()
        assert service.status == ServiceStatus.ACTIVE

    def test_version_increments_on_activate(self):
        service = UserService(abonent_id=uuid4(), service_type="internet")
        assert service.version == 1

        service.activate()
        assert service.version == 2

    def test_version_increments_on_deactivate(self):
        service = UserService(abonent_id=uuid4(), service_type="internet")
        service.activate()
        assert service.version == 2

        service.deactivate()
        assert service.version == 3

    def test_version_preserved_on_creation(self):
        service = UserService(
            abonent_id=uuid4(),
            service_type="voice",
            version=5,
        )

        assert service.version == 5


class TestUserServiceStatusChecks:
    """Тесты проверки статуса."""

    def test_is_active_true(self):
        """Проверка is_active для активной услуги."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )
        service.activate()

        assert service.is_active is True

    def test_is_active_false(self):
        """Проверка is_active для неактивной услуги."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
            status=ServiceStatus.DEACTIVATED,
        )

        assert service.is_active is False


class TestUserServiceProperties:
    """Тесты свойств услуги."""

    def test_default_currency(self):
        """Валюта по умолчанию — RUB."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="internet",
        )

        assert service.currency == "RUB"

    def test_custom_cost(self):
        """Пользовательская стоимость."""
        service = UserService(
            abonent_id=uuid4(),
            service_type="voice",
            cost=250.50,
            currency="RUB",
        )

        assert service.cost == 250.50
        assert service.currency == "RUB"


class TestUserServiceVersioning:
    """Тесты версионирования."""

    def test_version_increments_on_activate(self):
        service = UserService(abonent_id=uuid4(), service_type="internet")
        assert service.version == 1

        service.activate()
        assert service.version == 2

    def test_version_increments_on_deactivate(self):
        service = UserService(abonent_id=uuid4(), service_type="internet")
        service.activate()
        assert service.version == 2

        service.deactivate()
        assert service.version == 3

    def test_version_preserved_on_creation(self):
        service = UserService(
            abonent_id=uuid4(),
            service_type="voice",
            version=5,
        )

        assert service.version == 5
