# =============================================================================
# shm-next — Integration Tests: User Service Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.service import UserService
from app.core.domain.value_objects import Money, ServiceStatus
from app.infrastructure.db.repositories.abonent_repo import AbonentRepository
from app.infrastructure.db.repositories.service_repo import ServiceRepository


class TestServiceRepository:

    async def _create_abonent(self, db_session) -> Abonent:
        abonent_repo = AbonentRepository(db_session)
        abonent = Abonent(
            full_name="Test Abonent", phone="+79001112233",
            account_number="90001", balance=Money(1000, "RUB"),
        )
        return await abonent_repo.save(abonent)

    async def _create_service(self, db_session, abonent_id: UUID = None) -> UserService:
        service_repo = ServiceRepository(db_session)
        if abonent_id is None:
            abonent = await self._create_abonent(db_session)
            abonent_id = abonent.id
        service = UserService(
            abonent_id=abonent_id,
            service_type="internet",
            status=ServiceStatus.ACTIVE,
            cost=100.0,
            currency="RUB",
        )
        return await service_repo.save(service)

    async def test_create_and_get_service(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        service = UserService(
            abonent_id=abonent.id,
            service_type="internet",
            status=ServiceStatus.ACTIVE,
            cost=100.0,
            currency="RUB",
        )
        saved = await repo.save(service)
        assert saved.id is not None
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.abonent_id == service.abonent_id
        assert retrieved.service_type == "internet"
        assert retrieved.cost == 100.0

    async def test_get_nonexistent_service(self, db_session):
        repo = ServiceRepository(db_session)
        import uuid
        result = await repo.get(uuid.uuid4())
        assert result is None

    async def test_get_by_abonent(self, db_session):
        repo = ServiceRepository(db_session)
        # Create a service
        service = await self._create_service(db_session)
        
        # Get services by abonent_id
        services = await repo.get_by_abonent(service.abonent_id, active_only=False)
        assert len(services) == 1
        assert services[0].id == service.id

    async def test_activate_service(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        # Create service in INIT status
        service = UserService(
            abonent_id=abonent.id,
            service_type="internet",
            status=ServiceStatus.INIT,
            cost=100.0,
            currency="RUB",
        )
        saved = await repo.save(service)
        
        # Activate the service
        saved.activate()
        updated = await repo.save(saved)
        
        assert updated.id == saved.id
        assert updated.status == ServiceStatus.ACTIVE
        
        # Verify the update persisted
        retrieved = await repo.get(saved.id)
        assert retrieved is not None
        assert retrieved.status == ServiceStatus.ACTIVE

    async def test_get_by_status_active_only(self, db_session):
        repo = ServiceRepository(db_session)
        abonent = await self._create_abonent(db_session)
        # Create active service
        active_service = UserService(
            abonent_id=abonent.id,
            service_type="internet",
            status=ServiceStatus.ACTIVE,
            cost=100.0,
            currency="RUB",
        )
        await repo.save(active_service)
        
        # Create deactivated service
        deactivated_service = UserService(
            abonent_id=abonent.id,
            service_type="tv",
            status=ServiceStatus.DEACTIVATED,
            cost=50.0,
            currency="RUB",
        )
        await repo.save(deactivated_service)
        
        # Get only active services
        active_services = await repo.get_by_abonent(abonent.id, active_only=True)
        assert len(active_services) == 1
        assert active_services[0].id == active_service.id