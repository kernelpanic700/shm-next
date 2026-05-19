# =============================================================================
# shm-next — Integration Tests: TariffService Repository
# =============================================================================
from __future__ import annotations

import uuid

from app.core.domain.entities.tariff import Tariff
from app.core.domain.entities.tariff_service import TariffService
from app.core.domain.value_objects import Money
from app.infrastructure.db.repositories.tariff_repo import TariffRepository
from app.infrastructure.db.repositories.tariff_service_repo import TariffServiceRepository


class TestTariffServiceRepository:

    async def _create_tariff(self, db_session, name: str | None = None) -> Tariff:
        repo = TariffRepository(db_session)
        tariff = Tariff(name=name or f"Тестовый Тариф {uuid.uuid4().hex[:8]}", description="Для тестов", is_active=True, price=500.0)
        return await repo.save(tariff)

    async def test_create_and_get_tariff_service(self, db_session):
        repo = TariffServiceRepository(db_session)
        tariff = await self._create_tariff(db_session)
        service = TariffService(
            tariff_id=tariff.id, service_type="voice", name="Голосовая связь",
            cost=Money(200, "RUB"), billing_period="monthly", is_optional=False,
        )
        saved = await repo.save(service)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.tariff_id == tariff.id
        assert retrieved.service_type == "voice"
        assert retrieved.name == "Голосовая связь"
        assert float(retrieved.cost.amount) == 200.0

    async def test_get_nonexistent_tariff_service(self, db_session):
        repo = TariffServiceRepository(db_session)
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_tariff(self, db_session):
        repo = TariffServiceRepository(db_session)
        tariff = await self._create_tariff(db_session)
        for svc_type in ["voice", "data", "sms"]:
            service = TariffService(tariff_id=tariff.id, service_type=svc_type, cost=Money(100, "RUB"))
            await repo.save(service)
        services = await repo.get_by_tariff(tariff.id)
        assert len(services) == 3

    async def test_get_by_service_type(self, db_session):
        repo = TariffServiceRepository(db_session)
        tariff1 = await self._create_tariff(db_session)
        tariff2 = await self._create_tariff(db_session)
        voice1 = TariffService(tariff_id=tariff1.id, service_type="voice", name="Voice 1", cost=Money(100, "RUB"))
        voice2 = TariffService(tariff_id=tariff2.id, service_type="voice", name="Voice 2", cost=Money(150, "RUB"))
        data = TariffService(tariff_id=tariff1.id, service_type="data", name="Data 1", cost=Money(200, "RUB"))
        await repo.save(voice1)
        await repo.save(voice2)
        await repo.save(data)
        voice_services = await repo.get_by_service_type("voice")
        assert len(voice_services) == 2
        data_services = await repo.get_by_service_type("data")
        assert len(data_services) == 1

    async def test_get_by_service_type_with_tariff(self, db_session):
        repo = TariffServiceRepository(db_session)
        tariff1 = await self._create_tariff(db_session)
        tariff2 = await self._create_tariff(db_session)
        svc1 = TariffService(tariff_id=tariff1.id, service_type="voice", name="Voice T1", cost=Money(100, "RUB"))
        svc2 = TariffService(tariff_id=tariff2.id, service_type="voice", name="Voice T2", cost=Money(200, "RUB"))
        await repo.save(svc1)
        await repo.save(svc2)
        filtered = await repo.get_by_service_type("voice", tariff_id=tariff1.id)
        assert len(filtered) == 1
        assert filtered[0].tariff_id == tariff1.id

    async def test_update_cost(self, db_session):
        repo = TariffServiceRepository(db_session)
        tariff = await self._create_tariff(db_session)
        service = TariffService(tariff_id=tariff.id, service_type="voice", cost=Money(100, "RUB"))
        saved = await repo.save(service)
        initial_version = saved.version
        saved.update_cost(Money(250, "RUB"))
        updated = await repo.save(saved)
        assert float(updated.cost.amount) == 250.0
        assert updated.version == initial_version + 1

    async def test_set_sort_order(self, db_session):
        repo = TariffServiceRepository(db_session)
        tariff = await self._create_tariff(db_session)
        service = TariffService(tariff_id=tariff.id, service_type="voice", cost=Money(100, "RUB"))
        saved = await repo.save(service)
        assert saved.sort_order == 0
        saved.set_sort_order(5)
        updated = await repo.save(saved)
        assert updated.sort_order == 5
