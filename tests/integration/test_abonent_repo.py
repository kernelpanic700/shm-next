# =============================================================================
# shm-next — Integration Tests: Abonent Repository
# =============================================================================
from __future__ import annotations

from app.core.domain.entities.abonent import Abonent
from app.core.domain.value_objects import AbonentStatus, Money
from app.infrastructure.db.repositories.abonent_repo import AbonentRepository


class TestAbonentRepository:

    async def _create_abonent(self, db_session) -> Abonent:
        abonent_repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Тест Абонент",
            phone="+79001112233",
            account_number="90001",
            balance=Money(1000, "RUB"),
        )
        return await abonent_repo.save(abonent)

    async def test_create_and_get_abonent(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Иванов Иван Иванович",
            phone="+79001234567",
            account_number="10001",
            balance=Money(1000, "RUB"),
        )
        saved = await repo.save(abonent)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.full_name == "Иванов Иван Иванович"
        assert float(retrieved.balance.amount) == 1000.0

    async def test_get_nonexistent_abonent(self, db_session):
        repo = AbonentRepository(db_session)
        import uuid
        result = await repo.get(uuid.uuid4())
        assert result is None

    async def test_get_by_phone(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Петров Пётр Петрович",
            phone="+79009876543",
            account_number="10002",
            balance=Money(500, "RUB"),
        )
        await repo.save(abonent)
        retrieved = await repo.get_by_phone("+79009876543")
        assert retrieved is not None
        assert retrieved.full_name == "Петров Пётр Петрович"

    async def test_get_by_account(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Сидоров Сидор Сидорович",
            phone="+79005555555",
            account_number="10003",
            balance=Money(200, "RUB"),
        )
        await repo.save(abonent)
        retrieved = await repo.get_by_account("10003")
        assert retrieved is not None
        assert retrieved.full_name == "Сидоров Сидор Сидорович"

    async def test_list_abonents(self, db_session):
        repo = AbonentRepository(db_session)
        for i in range(5):
            abonent = Abonent(
                full_name=f"Абонент {i}",
                phone=f"+790000000{i}",
                account_number=f"2000{i}",
                balance=Money(100 * (i + 1), "RUB"),
            )
            await repo.save(abonent)
        abonents = await repo.list(offset=0, limit=10)
        assert len(abonents) == 5

    async def test_list_abonents_with_status_filter(self, db_session):
        repo = AbonentRepository(db_session)
        active = Abonent(
            full_name="Активный", phone="+79001111111",
            account_number="30001", balance=Money(100, "RUB"),
            status=AbonentStatus.ACTIVE,
        )
        blocked = Abonent(
            full_name="Заблокированный", phone="+79002222222",
            account_number="30002", balance=Money(200, "RUB"),
            status=AbonentStatus.BLOCKED,
        )
        await repo.save(active)
        await repo.save(blocked)
        active_only = await repo.list(offset=0, limit=50, status="ACTIVE")
        assert all(a.status == AbonentStatus.ACTIVE for a in active_only)

    async def test_update_abonent(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Исходное Имя", phone="+79003333333",
            account_number="40001", balance=Money(0, "RUB"),
        )
        saved = await repo.save(abonent)
        saved.update_info(full_name="Обновлённое Имя")
        updated = await repo.save(saved)
        assert updated.full_name == "Обновлённое Имя"

    async def test_delete_abonent(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="К удалению", phone="+79004444444",
            account_number="50001", balance=Money(0, "RUB"),
        )
        saved = await repo.save(abonent)
        result = await repo.delete(saved.id)
        assert result is True
        retrieved = await repo.get(saved.id)
        assert retrieved is None

    async def test_exists_abonent(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Для проверки", phone="+79006666666",
            account_number="60001", balance=Money(0, "RUB"),
        )
        saved = await repo.save(abonent)
        assert await repo.exists(saved.id) is True
        import uuid
        assert await repo.exists(uuid.uuid4()) is False

    async def test_change_balance(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Баланс", phone="+79007777777",
            account_number="70001", balance=Money(1000, "RUB"),
        )
        saved = await repo.save(abonent)
        saved.change_balance(Money(-200, "RUB"), reason="Оплата")
        updated = await repo.save(saved)
        assert float(updated.balance.amount) == 800.0

    async def test_assign_tariff(self, db_session):
        repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Без тарифа", phone="+79008888888",
            account_number="80001", balance=Money(0, "RUB"),
        )
        saved = await repo.save(abonent)
        assert saved.tariff_id is None
        import uuid
        saved.assign_tariff(uuid.uuid4())
        updated = await repo.save(saved)
        assert updated.tariff_id is not None
