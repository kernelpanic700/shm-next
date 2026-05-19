# =============================================================================
# shm-next — Integration Tests: Tariff Repository
# =============================================================================
from __future__ import annotations

from app.core.domain.entities.tariff import Tariff
from app.infrastructure.db.repositories.tariff_repo import TariffRepository


class TestTariffRepository:

    async def test_create_and_get_tariff(self, db_session):
        repo = TariffRepository(db_session)
        tariff = Tariff(
            name="Базовый", description="Базовый тарифный план",
            is_active=True, price=500.0, currency="RUB",
            billing_period="monthly", services=[{"type": "voice", "cost": 200}],
        )
        saved = await repo.save(tariff)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.name == "Базовый"
        assert retrieved.price == 500.0
        assert retrieved.currency == "RUB"
        assert retrieved.billing_period == "monthly"

    async def test_get_nonexistent_tariff(self, db_session):
        repo = TariffRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_name(self, db_session):
        repo = TariffRepository(db_session)
        tariff = Tariff(name="Премиум", description="Премиум тариф", is_active=True, price=1000.0)
        await repo.save(tariff)
        retrieved = await repo.get_by_name("Премиум")
        assert retrieved is not None
        assert retrieved.name == "Премиум"
        assert retrieved.price == 1000.0

    async def test_get_by_name_not_found(self, db_session):
        repo = TariffRepository(db_session)
        assert await repo.get_by_name("Несуществующий") is None

    async def test_list_tariffs(self, db_session):
        repo = TariffRepository(db_session)
        for i in range(3):
            tariff = Tariff(name=f"Тариф {i}", is_active=True, price=100 * (i + 1))
            await repo.save(tariff)
        tariffs = await repo.list(active_only=True)
        assert len(tariffs) == 3

    async def test_list_inactive_tariffs(self, db_session):
        repo = TariffRepository(db_session)
        active = Tariff(name="Активный", is_active=True, price=100)
        inactive = Tariff(name="Неактивный", is_active=False, price=200)
        await repo.save(active)
        await repo.save(inactive)
        tariffs = await repo.list(active_only=True)
        assert all(t.is_active for t in tariffs)

    async def test_list_all_tariffs(self, db_session):
        repo = TariffRepository(db_session)
        active = Tariff(name="Активный", is_active=True, price=100)
        inactive = Tariff(name="Неактивный", is_active=False, price=200)
        await repo.save(active)
        await repo.save(inactive)
        tariffs = await repo.list(active_only=False)
        assert len(tariffs) == 2

    async def test_update_tariff(self, db_session):
        repo = TariffRepository(db_session)
        tariff = Tariff(name="Старый", is_active=True, price=100)
        saved = await repo.save(tariff)
        saved.name = "Новый"
        saved.price = 500.0
        updated = await repo.save(saved)
        assert updated.name == "Новый"
        assert updated.price == 500.0

    async def test_tariff_version_increment(self, db_session):
        repo = TariffRepository(db_session)
        tariff = Tariff(name="Тариф", is_active=True, price=100)
        saved = await repo.save(tariff)
        initial_version = saved.version
        saved.is_active = False
        updated = await repo.save(saved)
        assert updated.version == initial_version + 1
