# =============================================================================
# shm-next — Unit Tests: Discount Entity
# =============================================================================
"""Тесты для Discount."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.domain.entities.discount import Discount
from app.core.domain.value_objects import Money


class TestDiscount:
    """Тесты Discount."""

    def test_create_default(self):
        discount = Discount()
        assert discount.id is not None
        assert discount.name == ""
        assert discount.discount_type == "percent"
        assert discount.value == 0.0
        assert discount.is_active is True

    def test_create_with_params(self):
        disc_id = uuid4()
        discount = Discount(
            id=disc_id,
            name="Summer Sale",
            description="Summer discount",
            discount_type="percent",
            value=15.0,
            currency="RUB",
            is_active=True,
        )
        assert discount.id == disc_id
        assert discount.name == "Summer Sale"
        assert discount.value == 15.0
        assert discount.currency == "RUB"

    def test_is_valid_at_active(self):
        now = datetime.now(timezone.utc)
        discount = Discount(
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=1),
            is_active=True,
        )
        assert discount.is_valid_at(now) is True

    def test_is_valid_at_inactive(self):
        discount = Discount(is_active=False)
        assert discount.is_valid_at(datetime.now(timezone.utc)) is False

    def test_is_valid_at_before_start(self):
        now = datetime.now(timezone.utc)
        discount = Discount(
            valid_from=now + timedelta(days=1),
            is_active=True,
        )
        assert discount.is_valid_at(now) is False

    def test_is_valid_at_after_end(self):
        now = datetime.now(timezone.utc)
        discount = Discount(
            valid_to=now - timedelta(days=1),
            is_active=True,
        )
        assert discount.is_valid_at(now) is False

    def test_is_valid_at_max_uses_reached(self):
        discount = Discount(max_uses=3, used_count=3, is_active=True)
        assert discount.is_valid_at(datetime.now(timezone.utc)) is False

    def test_is_valid_at_unlimited_uses(self):
        discount = Discount(max_uses=None, used_count=100, is_active=True)
        assert discount.is_valid_at(datetime.now(timezone.utc)) is True

    def test_apply_percent_discount(self):
        discount = Discount(discount_type="percent", value=10.0, currency="RUB")
        amount = Money(100, "RUB")
        result = discount.apply_to(amount)
        assert result.amount == 90

    def test_apply_fixed_discount(self):
        discount = Discount(discount_type="fixed", value=20.0, currency="RUB")
        amount = Money(100, "RUB")
        result = discount.apply_to(amount)
        assert result.amount == 80

    def test_apply_discount_not_negative(self):
        discount = Discount(discount_type="fixed", value=150.0, currency="RUB")
        amount = Money(100, "RUB")
        result = discount.apply_to(amount)
        assert result.amount == 0

    def test_apply_inactive_raises(self):
        discount = Discount(is_active=False)
        amount = Money(100, "RUB")
        try:
            discount.apply_to(amount)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_increment_usage(self):
        discount = Discount(max_uses=5, used_count=2)
        discount.increment_usage()
        assert discount.used_count == 3
        assert discount.version == 2

    def test_deactivate(self):
        discount = Discount(is_active=True)
        discount.deactivate()
        assert discount.is_active is False
        assert discount.version == 2
