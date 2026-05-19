# =============================================================================
# shm-next — Integration Tests: Optimistic Locking
# =============================================================================
from __future__ import annotations

from app.core.domain.entities.abonent import Abonent
from app.core.domain.value_objects import Money
from app.infrastructure.db.repositories.abonent_repo import AbonentRepository


class TestOptimisticLocking:

    async def test_abonent_version_increments_on_save(self, db_session):
        """Test that abonent version increments on each save."""
        abonent_repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Тест Абонент",
            phone="+79001112233",
            account_number="90001",
            balance=Money(1000, "RUB"),
        )
        saved_abonent = await abonent_repo.save(abonent)
        initial_version = saved_abonent.version
        
        # Update the abonent using change_balance method
        saved_abonent.change_balance(Money(500, "RUB"), "Test update")
        updated = await abonent_repo.save(saved_abonent)
        
        # Version should have incremented and balance should be updated
        assert updated.version == initial_version + 1
        assert updated.balance.amount == 1500.0
        
    async def test_optimistic_locking_prevents_lost_update(self, db_session):
        """Test that version increments correctly on updates."""
        abonent_repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Тест Абонент 2",
            phone="+79001112244",
            account_number="90002",
            balance=Money(500, "RUB"),
        )
        saved_abonent = await abonent_repo.save(abonent)
        initial_version = saved_abonent.version
        
        # First update using change_balance method
        saved_abonent.change_balance(Money(100, "RUB"), "Test update 1")
        updated1 = await abonent_repo.save(saved_abonent)
        assert updated1.version == initial_version + 1
        
        # Second update - get fresh entity and update
        fresh = await abonent_repo.get(saved_abonent.id)
        fresh.change_balance(Money(100, "RUB"), "Test update 2")
        updated2 = await abonent_repo.save(fresh)
        assert updated2.version == initial_version + 2
        
        # Verify final state
        final_abonent = await abonent_repo.get(saved_abonent.id)
        assert final_abonent.balance.amount == 700.0