# =============================================================================
# shm-next — Unit Tests: Abonent Entity
# =============================================================================
"""Тесты для сущности Abonent."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.domain.entities.abonent import Abonent, AbonentCreate, AbonentUpdate
from app.core.domain.value_objects import AbonentStatus, Money


class TestAbonentCreate:
    """Тесты DTO AbonentCreate."""

    def test_create(self):
        data = AbonentCreate(
            full_name="Иванов Иван Иванович",
            phone="+79991234567",
            account_number="12345",
            balance=1000.0,
            currency="RUB",
        )
        assert data.full_name == "Иванов Иван Иванович"
        assert data.phone == "+79991234567"
        assert data.balance == 1000.0


class TestAbonentUpdate:
    """Тесты DTO AbonentUpdate."""

    def test_create_with_changes(self):
        data = AbonentUpdate(full_name="Новое имя", status="BLOCKED")
        assert data.full_name == "Новое имя"
        assert data.status == "BLOCKED"

    def test_create_empty(self):
        data = AbonentUpdate()
        assert data.full_name is None
        assert data.status is None


class TestAbonent:
    """Тесты сущности Abonent."""

    def test_create_default(self):
        abonent = Abonent()
        assert abonent.id is not None
        assert abonent.full_name == ""
        assert abonent.balance.amount == 0
        assert abonent.status == AbonentStatus.ACTIVE

    def test_create_with_params(self):
        abonent_id = uuid4()
        abonent = Abonent(
            id=abonent_id,
            full_name="Тест Абонент",
            phone="+79990000000",
            account_number="ACC001",
            balance=Money(500, "RUB"),
            status=AbonentStatus.ACTIVE,
        )
        assert abonent.id == abonent_id
        assert abonent.full_name == "Тест Абонент"
        assert abonent.phone == "+79990000000"
        assert abonent.account_number == "ACC001"
        assert abonent.balance.amount == 500

    def test_assign_tariff(self):
        abonent = Abonent()
        tariff_id = uuid4()
        abonent.assign_tariff(tariff_id)
        assert abonent.tariff_id == tariff_id
        assert abonent.version == 2

    def test_change_balance_positive(self):
        abonent = Abonent(balance=Money(100, "RUB"))
        abonent.change_balance(Money(50, "RUB"), reason="Пополнение")
        assert abonent.balance.amount == 150
        assert abonent.version == 2

    def test_change_balance_negative_allowed(self):
        abonent = Abonent(balance=Money(100, "RUB"), allow_negative=True)
        abonent.change_balance(Money(-150, "RUB"), reason="Списание")
        assert abonent.balance.amount == -50

    def test_change_balance_negative_not_allowed(self):
        abonent = Abonent(balance=Money(100, "RUB"), allow_negative=False)
        with pytest.raises(ValueError, match="cannot be negative"):
            abonent.change_balance(Money(-150, "RUB"), reason="Списание")

    def test_change_balance_currency_mismatch(self):
        abonent = Abonent(balance=Money(100, "RUB"))
        with pytest.raises(ValueError, match="Currency mismatch"):
            abonent.change_balance(Money(50, "USD"), reason="Test")

    def test_activate(self):
        abonent = Abonent(status=AbonentStatus.BLOCKED)
        abonent.activate()
        assert abonent.status == AbonentStatus.ACTIVE

    def test_block(self):
        abonent = Abonent(status=AbonentStatus.ACTIVE)
        abonent.block()
        assert abonent.status == AbonentStatus.BLOCKED

    def test_deactivate(self):
        abonent = Abonent(status=AbonentStatus.ACTIVE)
        abonent.deactivate()
        assert abonent.status == AbonentStatus.DISABLED

    def test_version_increment(self):
        abonent = Abonent(version=1)
        initial_version = abonent.version
        abonent.activate()
        assert abonent.version == initial_version + 1
