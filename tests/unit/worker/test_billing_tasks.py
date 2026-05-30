from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.domain.entities import Abonent, CatalogService, UserService
from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.core.domain.value_objects import AbonentStatus, Money, ServiceStatus
from app.worker.tasks.billing import mark_overdue_invoices, run_billing_cycle, run_shm_auto_renewal


class FakeServiceRepo:
    def __init__(self, service: UserService, abonent: Abonent) -> None:
        self.service = service
        self.abonent = abonent
        self.requested_limit: int | None = None

    async def get_expiring_auto_bill(self, cutoff: datetime, limit: int = 100) -> list[UserService]:
        self.requested_limit = limit
        return [self.service]

    async def get(self, service_id):
        return self.service if service_id == self.service.id else None

    async def get_abonent(self, abonent_id):
        return self.abonent if abonent_id == self.abonent.id else None

    async def save(self, service: UserService) -> UserService:
        self.service = service
        return service

    async def save_abonent(self, abonent: Abonent) -> Abonent:
        self.abonent = abonent
        return abonent


class FakeCatalogRepo:
    def __init__(self, catalog: CatalogService) -> None:
        self.catalog = catalog

    async def get(self, catalog_id):
        return self.catalog if catalog_id == self.catalog.id else None


class FakeRuleRepo:
    async def get_matching(self, **kwargs) -> list:
        return []


class FakeSpoolRepo:
    pass


class FakeUnitOfWork:
    def __init__(self, service: UserService, abonent: Abonent, catalog: CatalogService) -> None:
        self.services = FakeServiceRepo(service, abonent)
        self.catalog_services = FakeCatalogRepo(catalog)
        self.event_action_rules = FakeRuleRepo()
        self.spool = FakeSpoolRepo()
        self.commit_count = 0
        self.rollback_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit_count += 1
        else:
            self.rollback_count += 1


class FakeInvoiceRepo:
    def __init__(self, invoices: list[Invoice]) -> None:
        self.invoices = invoices
        self.requested_limit: int | None = None
        self.saved: list[Invoice] = []

    async def get_due_for_overdue(self, now: datetime, limit: int = 100) -> list[Invoice]:
        self.requested_limit = limit
        return self.invoices[:limit]

    async def save(self, invoice: Invoice) -> Invoice:
        self.saved.append(invoice)
        return invoice


class FakeInvoiceUnitOfWork:
    def __init__(self, invoices: list[Invoice]) -> None:
        self.invoices = FakeInvoiceRepo(invoices)
        self.commit_count = 0
        self.rollback_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit_count += 1
        else:
            self.rollback_count += 1


class FakeCycleAbonentRepo:
    def __init__(self, abonent: Abonent) -> None:
        self.abonent = abonent
        self.requested_offset: int | None = None
        self.requested_limit: int | None = None

    async def list_active(self, offset: int = 0, limit: int = 50) -> list[Abonent]:
        self.requested_offset = offset
        self.requested_limit = limit
        return [self.abonent]

    async def get(self, abonent_id):
        return self.abonent if abonent_id == self.abonent.id else None

    async def save(self, abonent: Abonent) -> Abonent:
        self.abonent = abonent
        return abonent


class FakeCycleBillingRepo:
    def __init__(self, service: UserService) -> None:
        self.service = service

    async def get_abonent_services(self, abonent_id, active_only: bool = True) -> list[UserService]:
        return [self.service]


class FakeCycleWithdrawRepo:
    def __init__(self) -> None:
        self.created: list[dict] = []

    async def create_withdraw(self, **kwargs):
        withdraw_id = uuid4()
        self.created.append({**kwargs, "withdraw_id": withdraw_id})
        return withdraw_id


class FakeCycleInvoiceRepo:
    def __init__(self) -> None:
        self.saved: list[Invoice] = []

    async def save(self, invoice: Invoice) -> Invoice:
        self.saved.append(invoice)
        return invoice


class FakeCycleBonusRepo:
    async def get_usable_by_abonent(self, abonent_id, at) -> list:
        return []


class FakeBillingCycleUnitOfWork:
    def __init__(self, service: UserService, abonent: Abonent) -> None:
        self.abonents = FakeCycleAbonentRepo(abonent)
        self.billing = FakeCycleBillingRepo(service)
        self.services = object()
        self.withdraws = FakeCycleWithdrawRepo()
        self.invoices = FakeCycleInvoiceRepo()
        self.bonus_entries = FakeCycleBonusRepo()
        self.commit_count = 0
        self.rollback_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit_count += 1
        else:
            self.rollback_count += 1


@pytest.mark.asyncio
async def test_run_shm_auto_renewal_with_injected_uow() -> None:
    abonent_id = uuid4()
    catalog_id = uuid4()
    now = datetime(2026, 6, 1, tzinfo=UTC)
    service = UserService(
        abonent_id=abonent_id,
        service_type="internet",
        catalog_service_id=catalog_id,
        status=ServiceStatus.ACTIVE,
        activated_at=datetime(2026, 5, 1, tzinfo=UTC),
        expire_at=now,
        cost=500.0,
        period_cost="1.0000",
        auto_bill=True,
    )
    abonent = Abonent(
        id=abonent_id,
        full_name="Active",
        phone="+79990000017",
        balance=Money("1000.00"),
        status=AbonentStatus.ACTIVE,
    )
    catalog = CatalogService(
        id=catalog_id,
        name="Internet 100M",
        cost=Money("500.00"),
        period_cost="1.0000",
    )
    uow = FakeUnitOfWork(service, abonent, catalog)

    result = await run_shm_auto_renewal(limit=25, uow=uow)

    assert result["status"] == "success"
    assert result["processed"] == 1
    assert result["renewed"] == 1
    assert result["suspended"] == 0
    assert result["failed"] == 0
    assert uow.services.requested_limit == 25
    assert uow.services.service.expire_at and uow.services.service.expire_at > now
    assert uow.services.abonent.balance == Money("500.00")
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_run_billing_cycle_with_injected_uow() -> None:
    abonent_id = uuid4()
    service = UserService(
        abonent_id=abonent_id,
        service_type="internet",
        status=ServiceStatus.ACTIVE,
        activated_at=datetime(2026, 5, 1, tzinfo=UTC),
        cost=300.0,
    )
    abonent = Abonent(
        id=abonent_id,
        full_name="Active",
        phone="+79990000018",
        balance=Money("1000.00"),
        status=AbonentStatus.ACTIVE,
    )
    uow = FakeBillingCycleUnitOfWork(service, abonent)

    result = await run_billing_cycle(
        period_start=datetime(2026, 5, 1, tzinfo=UTC).date(),
        period_end=datetime(2026, 5, 1, tzinfo=UTC).date(),
        offset=2,
        limit=15,
        uow=uow,
    )

    assert result["status"] == "success"
    assert result["processed"] == 1
    assert result["withdraw_count"] == 1
    assert result["invoice_count"] == 1
    assert uow.abonents.requested_offset == 2
    assert uow.abonents.requested_limit == 15
    assert len(uow.withdraws.created) == 1
    assert len(uow.invoices.saved) == 1
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_mark_overdue_invoices_with_injected_uow() -> None:
    invoice = Invoice(
        abonent_id=uuid4(),
        amount=100,
        status=InvoiceStatus.ISSUED,
        due_date=datetime(2026, 1, 1, tzinfo=UTC),
    )
    uow = FakeInvoiceUnitOfWork([invoice])

    result = await mark_overdue_invoices(limit=10, uow=uow)

    assert result == {"status": "success", "marked_overdue": 1}
    assert invoice.status == InvoiceStatus.OVERDUE
    assert uow.invoices.saved == [invoice]
    assert uow.invoices.requested_limit == 10
    assert uow.commit_count == 1
