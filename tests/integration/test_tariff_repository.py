# =============================================================================
# shm-next — Integration Tests: Tariff Repository
# =============================================================================
from __future__ import annotations

from app.core.domain.entities.tariff import Tariff
from app.infrastructure.db.repositories.tariff_repo import TariffRepository


class TestTariffRepository:

    async def _create_tariff(self, db_session) -> Tariff:
        tariff_repo = TariffRepository(db_session)
        tariff = Tariff(
            name="Test Tariff",
            description="Test tariff description",
            price=500.0,
            currency="RUB",
            is_active=True,
            billing_period="monthly",
            services=["internet", "tv"],
        )
        return await tariff_repo.save(tariff)

    async def test_create_and_get_tariff(self, db_session):
        repo = TariffRepository(db_session)
        tariff = Tariff(
            name="Премиум тариф",
            description="Премиум тариф с высокой скоростью",
            price=1500.0,
            currency="RUB",
            is_active=True,
            billing_period="monthly",
            services=["internet", "tv", "telephony"],
        )
        saved = await repo.save(tariff)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.name == "Премиум тариф"
        assert retrieved.price == 1500.0
        assert retrieved.is_active == True
        assert retrieved.billing_period == "monthly"
        assert retrieved.services == ["internet", "tv", "telephony"]

    async def test_get_nonexistent_tariff(self, db_session):
        repo = TariffRepository(db_session)
        import uuid
        result = await repo.get(uuid.uuid4())
        assert result is None

    async def test_get_by_name(self, db_session):
        repo = TariffRepository(db_session)
        # Create a tariff
        tariff = await self._create_tariff(db_session)
        
        # Get tariff by name
        retrieved = await repo.get_by_name(tariff.name)
        assert retrieved is not None
        assert retrieved.id == tariff.id
        assert retrieved.name == tariff.name

    async def test_update_tariff(self, db_session):
        repo = TariffRepository(db_session)
        tariff = await self._create_tariff(db_session)
        
        # Update the tariff
        tariff.price = 750.0
        tariff.is_active = False
        updated = await repo.save(tariff)
        
        assert updated.id == tariff.id
        assert updated.price == 750.0
        assert updated.is_active == False
        
        # Verify the update persisted
        retrieved = await repo.get(tariff.id)
        assert retrieved is not None
        assert retrieved.price == 750.0
        assert retrieved.is_active == False

    async def test_get_active_tariffs(self, db_session):
        repo = TariffRepository(db_session)
        # Create active tariff
        active_tariff = await self._create_tariff(db_session)
        
        # Create inactive tariff
        inactive_tariff = Tariff(
            name="Архивный тариф",
            description="Старый тариф",
            price=200.0,
            currency="RUB",
            is_active=False,
            billing_period="monthly",
            services=["dialup"],
        )
        await repo.save(inactive_tariff)
        
        # Get only active tariffs
        active_tariffs = await repo.list(active_only=True)
        assert len(active_tariffs) >= 1
        assert any(t.id == active_tariff.id for t in active_tariffs)
        assert not any(t.id == inactive_tariff.id for t in active_tariffs)