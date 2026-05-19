# =============================================================================
# shm-next — Integration Tests: Discount Repository
# =============================================================================
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.domain.entities.discount import Discount, DiscountType
from app.core.domain.value_objects import Money
from app.infrastructure.db.repositories.discount_repo import DiscountRepository


class TestDiscountRepository:

    async def test_create_and_get_discount(self, db_session):
        repo = DiscountRepository(db_session)
        discount = Discount(name="Скидка 10%", description="Скидка для постоянных клиентов", discount_type=DiscountType.PERCENT, value=10.0, currency="RUB", is_active=True)
        saved = await repo.save(discount)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.name == "Скидка 10%"
        assert retrieved.discount_type == DiscountType.PERCENT
        assert retrieved.value == 10.0

    async def test_get_nonexistent_discount(self, db_session):
        repo = DiscountRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_active_discounts(self, db_session):
        repo = DiscountRepository(db_session)
        active = Discount(name="Активная", discount_type=DiscountType.PERCENT, value=10.0, is_active=True)
        inactive = Discount(name="Неактивная", discount_type=DiscountType.FIXED, value=50.0, is_active=False)
        await repo.save(active)
        await repo.save(inactive)
        discounts = await repo.get_active()
        assert len(discounts) == 1
        assert discounts[0].name == "Активная"

    async def test_get_valid_at(self, db_session):
        repo = DiscountRepository(db_session)
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=10)
        future = now + timedelta(days=10)
        expired_start = now - timedelta(days=30)
        expired_end = now - timedelta(days=10)
        valid = Discount(name="Действующая", discount_type=DiscountType.PERCENT, value=15.0, valid_from=past, valid_to=future, is_active=True)
        expired = Discount(name="Истёкшая", discount_type=DiscountType.PERCENT, value=20.0, valid_from=expired_start, valid_to=expired_end, is_active=True)
        await repo.save(valid)
        await repo.save(expired)
        result = await repo.get_valid_at(now)
        assert any(d.name == "Действующая" for d in result)
        assert not any(d.name == "Истёкшая" for d in result)

    async def test_update_discount(self, db_session):
        repo = DiscountRepository(db_session)
        discount = Discount(name="Старая", discount_type=DiscountType.PERCENT, value=5.0, is_active=True)
        saved = await repo.save(discount)
        # Create updated discount with new values
        updated_discount = Discount(
            id=saved.id,
            name="Новая",
            discount_type=DiscountType.PERCENT,
            value=15.0,
            is_active=True,
            version=saved.version + 1,
        )
        updated = await repo.save(updated_discount)
        assert updated.name == "Новая"
        assert updated.value == 15.0

    async def test_deactivate_discount(self, db_session):
        repo = DiscountRepository(db_session)
        discount = Discount(name="Активная", discount_type=DiscountType.PERCENT, value=10.0, is_active=True)
        saved = await repo.save(discount)
        saved.deactivate()
        updated = await repo.save(saved)
        assert updated.is_active is False

    async def test_discount_is_valid_at(self, db_session):
        repo = DiscountRepository(db_session)
        now = datetime.now(timezone.utc)
        discount = Discount(name="Тестовая", discount_type=DiscountType.PERCENT, value=10.0, valid_from=now - timedelta(days=5), valid_to=now + timedelta(days=5), is_active=True)
        saved = await repo.save(discount)
        assert saved.is_valid_at(now) is True

    async def test_discount_apply_to(self, db_session):
        repo = DiscountRepository(db_session)
        discount = Discount(name="10%", discount_type=DiscountType.PERCENT, value=10.0, is_active=True)
        saved = await repo.save(discount)
        amount = Money(1000, "RUB")
        discounted = saved.apply_to(amount)
        assert float(discounted.amount) == 900.0

    async def test_discount_max_uses(self, db_session):
        repo = DiscountRepository(db_session)
        discount = Discount(name="Лимитированная", discount_type=DiscountType.FIXED, value=100.0, is_active=True, max_uses=2, used_count=2)
        saved = await repo.save(discount)
        assert saved.is_valid_at(datetime.now(timezone.utc)) is False
