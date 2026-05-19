# =============================================================================
# shm-next — Integration Tests: Service Repository
# =============================================================================
from __future__ import annotations

from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.service import UserService
from app.core.domain.value_objects import Money, ServiceStatus
from app.infrastructure.db.repositories.abonent_repo import AbonentRepository
from app.infrastructure.db.repositories.service_repo import ServiceRepository


class TestServiceRepository:

    async def _create_abonent(self, db_session) -> Abonent:
        abonent_repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Тест Абонент", phone="+79001112233",
            account_number="90001", balance=Money(1000, "RUB"),
        )
        return await abonent_repo.save(abonent)

    async def test_create_and_get_service(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = UserService(
            abonent_id=abonent.id, service_type="voice",
            status=ServiceStatus.ACTIVE, cost=200.0, currency="RUB",
        )
        saved = await repo.save(service)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.service_type == "voice"
        assert retrieved.status == ServiceStatus.ACTIVE

    async def test_get_nonexistent_service(self, db_session):
        repo = ServiceRepository(db_session)
        import uuid
        assert await repo.get(uuid.uuid4()) is None

    async def test_get_by_abonent(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        for svc_type in ["voice", "data", "sms"]:
            service = UserService(
                abonent_id=abonent.id, service_type=svc_type,
                status=ServiceStatus.ACTIVE,
            )
            await repo.save(service)
        services = await repo.get_by_abonent(abonent.id, active_only=False)
        assert len(services) == 3

    async def test_get_by_abonent_active_only(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        active_service = UserService(
            abonent_id=abonent.id, service_type="voice",
            status=ServiceStatus.ACTIVE,
        )
        deactivated_service = UserService(
            abonent_id=abonent.id, service_type="data",
            status=ServiceStatus.DEACTIVATED,
        )
        await repo.save(active_service)
        await repo.save(deactivated_service)
        active_only = await repo.get_by_abonent(abonent.id, active_only=True)
        assert len(active_only) == 1
        assert active_only[0].service_type == "voice"

    async def test_get_active_by_abonent(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        voice1 = UserService(
            abonent_id=abonent.id, service_type="voice",
            status=ServiceStatus.ACTIVE,
        )
        voice2 = UserService(
            abonent_id=abonent.id, service_type="voice",
            status=ServiceStatus.ACTIVE,
        )
        data = UserService(
            abonent_id=abonent.id, service_type="data",
            status=ServiceStatus.ACTIVE,
        )
        await repo.save(voice1)
        await repo.save(voice2)
        await repo.save(data)
        voice_services = await repo.get_active_by_abonent(abonent.id, service_type="voice")
        assert len(voice_services) == 2
        data_services = await repo.get_active_by_abonent(abonent.id, service_type="data")
        assert len(data_services) == 1

    async def test_get_active_by_abonent_all_types(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        for svc_type in ["voice", "data", "sms"]:
            service = UserService(
                abonent_id=abonent.id, service_type=svc_type,
                status=ServiceStatus.ACTIVE,
            )
            await repo.save(service)
        all_active = await repo.get_active_by_abonent(abonent.id)
        assert len(all_active) == 3

    async def test_activate_service(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = UserService(
            abonent_id=abonent.id, service_type="voice",
            status=ServiceStatus.INIT,
        )
        saved = await repo.save(service)
        assert saved.status == ServiceStatus.INIT
        saved.activate()
        updated = await repo.save(saved)
        assert updated.status == ServiceStatus.ACTIVE

    async def test_deactivate_service(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = UserService(
            abonent_id=abonent.id, service_type="voice",
            status=ServiceStatus.ACTIVE,
        )
        saved = await repo.save(service)
        saved.deactivate(reason="По запросу")
        updated = await repo.save(saved)
        assert updated.status == ServiceStatus.DEACTIVATED

    async def test_get_abonent_from_service(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        retrieved = await repo.get_abonent(abonent.id)
        assert retrieved is not None
        assert retrieved.id == abonent.id
