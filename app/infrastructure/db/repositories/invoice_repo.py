# =============================================================================
# shm-next — Invoice Repository
# =============================================================================
"""Репозиторий счетов."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.core.domain.repositories.invoice import InvoiceRepositoryProtocol
from app.infrastructure.db.models import InvoiceModel


class InvoiceRepository(InvoiceRepositoryProtocol):
    """Репозиторий счетов."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, invoice_id: UUID) -> Invoice | None:
        """Получить счёт по ID."""
        model = await self._session.get(InvoiceModel, invoice_id)
        return self._to_domain(model) if model else None

    async def get_by_abonent(
        self,
        abonent_id: UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[Invoice]:
        """Получить счета абонента."""
        stmt = select(InvoiceModel).where(
            InvoiceModel.abonent_id == abonent_id
        )

        if from_date:
            stmt = stmt.where(InvoiceModel.created_at >= from_date)
        if to_date:
            stmt = stmt.where(InvoiceModel.created_at <= to_date)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list(
        self,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Invoice], int]:
        """Получить список счетов."""
        filters = []
        if status:
            filters.append(InvoiceModel.status == status)
        if from_date:
            filters.append(InvoiceModel.created_at >= from_date)
        if to_date:
            filters.append(InvoiceModel.created_at <= to_date)

        total_stmt = select(func.count()).select_from(InvoiceModel)
        stmt = select(InvoiceModel).order_by(InvoiceModel.created_at.desc())
        if filters:
            total_stmt = total_stmt.where(*filters)
            stmt = stmt.where(*filters)

        total_result = await self._session.execute(total_stmt)
        result = await self._session.execute(stmt.offset(offset).limit(limit))
        models = result.scalars().all()
        return [self._to_domain(m) for m in models], int(total_result.scalar_one())

    async def get_unpaid(self) -> list[Invoice]:
        """Получить неоплаченные счета."""
        stmt = select(InvoiceModel).where(
            InvoiceModel.status.in_(["DRAFT", "ISSUED", "SENT", "OVERDUE"])
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_overdue(self) -> list[Invoice]:
        """Получить просроченные счета."""
        from datetime import datetime

        now = datetime.now(UTC)
        stmt = select(InvoiceModel).where(
            InvoiceModel.status == "OVERDUE",
            InvoiceModel.due_date < now,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_due_for_overdue(
        self,
        now: datetime,
        limit: int = 100,
    ) -> list[Invoice]:
        """Получить счета, которые пора перевести в OVERDUE."""
        stmt = (
            select(InvoiceModel)
            .where(
                InvoiceModel.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.SENT]),
                InvoiceModel.due_date.is_not(None),
                InvoiceModel.due_date < now,
            )
            .order_by(InvoiceModel.due_date.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def save(self, invoice: Invoice) -> Invoice:
        """Сохранить счёт."""
        # Check if model exists
        existing = await self._session.get(InvoiceModel, invoice.id)
        if existing:
            # Update existing
            existing.abonent_id = invoice.abonent_id
            existing.amount = invoice.amount
            existing.currency = invoice.currency
            existing.status = invoice.status
            existing.period_start = invoice.period_start
            existing.period_end = invoice.period_end
            existing.due_date = invoice.due_date
            existing.description = invoice.description
            existing.meta = invoice.meta
            existing.version = invoice.version
            model = existing
        else:
            # Create new
            model = InvoiceModel(
                id=invoice.id,
                abonent_id=invoice.abonent_id,
                amount=invoice.amount,
                currency=invoice.currency,
                status=invoice.status,
                period_start=invoice.period_start,
                period_end=invoice.period_end,
                due_date=invoice.due_date,
                description=invoice.description,
                meta=invoice.meta,
                version=invoice.version,
            )
            self._session.add(model)

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: InvoiceModel) -> Invoice:
        """Конвертация модели в доменную сущность."""
        return Invoice(
            id=model.id,
            abonent_id=model.abonent_id,
            amount=model.amount,
            currency=model.currency,
            status=model.status,
            period_start=model.period_start,
            period_end=model.period_end,
            due_date=model.due_date,
            description=model.description,
            metadata=model.meta,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
