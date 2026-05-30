# =============================================================================
# shm-next — Service Application Service
# =============================================================================
"""
Application Service для управления услугами абонентов.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog

from app.core.domain.entities.catalog_service import CatalogService
from app.core.domain.entities.service import UserService
from app.core.domain.value_objects import ServiceStatus
from app.core.domain.repositories.catalog_service import (
    CatalogServiceRepositoryProtocol,
)
from app.core.domain.repositories.service import ServiceRepositoryProtocol
from app.core.domain.value_objects import Money
from app.core.services.billing_engine import BillingEngine, SHMBillingMode
from app.core.services.event_bus import EventBus

logger = structlog.get_logger("service_service")


class SHMAutoRenewalResult(dict):
    """Stats for SHM auto-renewal batch."""


class ServiceService:
    """
    Сервис управления услугами абонентов.

    Use Cases:
    - Подключение услуги
    - Отключение услуги
    - Получение списка услуг
    """

    def __init__(
        self,
        service_repo: ServiceRepositoryProtocol,
        event_bus: EventBus,
        catalog_service_repo: CatalogServiceRepositoryProtocol | None = None,
        billing_engine: BillingEngine | None = None,
    ) -> None:
        self._service_repo = service_repo
        self._event_bus = event_bus
        self._catalog_service_repo = catalog_service_repo
        self._billing_engine = billing_engine or BillingEngine()

    async def activate_service(
        self,
        abonent_id: UUID,
        service_type: str,
        tariff_service_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> UserService:
        """
        Подключить услугу абоненту.

        Args:
            abonent_id: ID абонента
            service_type: Тип услуги
            tariff_service_id: ID услуги тарифа (опционально)
            metadata: Дополнительные данные

        Returns:
            UserService: Созданная услуга
        """
        # Проверяем статус абонента перед подключением услуги
        abonent = await self._service_repo.get_abonent(abonent_id)
        if abonent is None:
            raise ValueError(f"Abonent {abonent_id} not found")
        if not abonent.status.is_active():
            raise ValueError(
                f"Cannot activate service for abonent in status: {abonent.status}"
            )

        service = UserService(
            abonent_id=abonent_id,
            service_type=service_type,
            tariff_service_id=tariff_service_id,
            metadata=metadata,
        )
        service.activate()

        saved = await self._service_repo.save(service)

        # Публикуем событие
        from app.core.domain.events.service_events import ServiceActivatedEvent

        event = ServiceActivatedEvent(
            abonent_id=str(abonent_id),
            service_id=str(saved.id),
            service_type=service_type,
        )
        await self._event_bus.publish(event)

        logger.info(
            "Service activated",
            abonent_id=abonent_id,
            service_type=service_type,
        )

        return saved

    async def order_catalog_service(
        self,
        abonent_id: UUID,
        catalog_service_id: UUID,
        quantity: int = 1,
        now: datetime | None = None,
        abonent_discount_percent: int = 0,
        bonus_balance: Money | None = None,
        metadata: dict | None = None,
    ) -> UserService:
        """
        Заказать услугу из каталога SHM.

        Выполняет базовый SHM-сценарий: проверяет доступность услуги,
        рассчитывает списание, меняет баланс, создает user_service со сроком
        действия и публикует событие активации.
        """
        catalog = await self._get_catalog_service(catalog_service_id)
        if not catalog.allow_to_order:
            raise ValueError(f"Catalog service {catalog_service_id} is not orderable")
        await self._ensure_catalog_service_limit(
            abonent_id=abonent_id,
            catalog=catalog,
            quantity=quantity,
        )

        abonent = await self._service_repo.get_abonent(abonent_id)
        if abonent is None:
            raise ValueError(f"Abonent {abonent_id} not found")
        if not abonent.status.is_active():
            raise ValueError(
                f"Cannot order service for abonent in status: {abonent.status}"
            )

        charge = self._billing_engine.calculate_shm_charge(
            cost=catalog.cost,
            quantity=quantity,
            abonent_discount_percent=0
            if catalog.no_discount
            else abonent_discount_percent,
            bonus_balance=bonus_balance,
        )

        if (
            not catalog.pay_in_credit
            and not abonent.allow_negative
            and abonent.balance < charge.total
        ):
            raise ValueError("Insufficient balance")

        if not charge.total.is_zero():
            abonent.change_balance(
                -charge.total,
                reason="shm_service_order",
                allow_credit=catalog.pay_in_credit,
            )
            await self._service_repo.save_abonent(abonent)

        starts_at = now or datetime.now(UTC)
        expire_at = self._billing_engine.calculate_shm_end_at(
            starts_at=starts_at,
            period_cost=catalog.period_cost,
            mode=SHMBillingMode.FIXED_30_DAYS,
        )
        service = self._build_user_service(
            abonent_id=abonent_id,
            catalog=catalog,
            quantity=quantity,
            starts_at=starts_at,
            expire_at=expire_at,
            paid_amount=charge.total,
            metadata={
                **(metadata or {}),
                "shm_charge": {
                    "subtotal": str(charge.subtotal.amount),
                    "discount": str(charge.discount.amount),
                    "bonus_used": str(charge.bonus_used.amount),
                    "total": str(charge.total.amount),
                },
            },
        )
        service.activate(starts_at)
        saved = await self._service_repo.save(service)

        for child_id in catalog.children:
            child = await self._get_catalog_service(child_id)
            child_service = self._build_user_service(
                abonent_id=abonent_id,
                catalog=child,
                quantity=1,
                starts_at=starts_at,
                expire_at=expire_at,
                paid_amount=Money.zero(catalog.cost.currency.value),
                parent_id=saved.id,
                metadata={"parent_catalog_service_id": str(catalog.id)},
            )
            child_service.activate(starts_at)
            await self._service_repo.save(child_service)

        from app.core.domain.events.service_events import ServiceActivatedEvent

        await self._event_bus.publish(
            ServiceActivatedEvent(
                abonent_id=str(abonent_id),
                service_id=str(saved.id),
                service_type=saved.service_type,
                catalog_service_id=str(saved.catalog_service_id)
                if saved.catalog_service_id
                else None,
                expires_at=saved.expire_at,
            )
        )

        logger.info(
            "SHM catalog service ordered",
            abonent_id=abonent_id,
            catalog_service_id=catalog_service_id,
            user_service_id=saved.id,
        )
        return saved

    async def renew_catalog_service(
        self,
        service_id: UUID,
        now: datetime | None = None,
        abonent_discount_percent: int = 0,
        bonus_balance: Money | None = None,
    ) -> UserService:
        """Продлить SHM-услугу абонента на следующий период."""
        service = await self._service_repo.get(service_id)
        if service is None:
            raise ValueError(f"Service {service_id} not found")
        if service.catalog_service_id is None:
            raise ValueError("Service is not linked to SHM catalog service")

        catalog = await self._get_catalog_service(service.catalog_service_id)
        abonent = await self._service_repo.get_abonent(service.abonent_id)
        if abonent is None:
            raise ValueError(f"Abonent {service.abonent_id} not found")

        charge = self._billing_engine.calculate_shm_charge(
            cost=catalog.cost,
            quantity=service.quantity,
            abonent_discount_percent=0
            if service.no_discount or catalog.no_discount
            else abonent_discount_percent,
            bonus_balance=bonus_balance,
        )
        if (
            not service.pay_in_credit
            and not abonent.allow_negative
            and abonent.balance < charge.total
        ):
            service.suspend(reason="insufficient_balance")
            await self._service_repo.save(service)
            raise ValueError("Insufficient balance")

        if not charge.total.is_zero():
            abonent.change_balance(
                -charge.total,
                reason="shm_service_renew",
                allow_credit=service.pay_in_credit,
            )
            await self._service_repo.save_abonent(abonent)

        renewal_base = max(
            now or datetime.now(UTC),
            service.expire_at or service.activated_at or datetime.now(UTC),
        )
        expire_at = self._billing_engine.calculate_shm_end_at(
            starts_at=renewal_base,
            period_cost=service.period_cost,
            mode=SHMBillingMode.FIXED_30_DAYS,
        )
        service.renew(expire_at=expire_at, cost=float(charge.total.amount))
        saved = await self._service_repo.save(service)

        from app.core.domain.events.service_events import ServiceRenewedEvent

        await self._event_bus.publish(
            ServiceRenewedEvent(
                abonent_id=str(service.abonent_id),
                service_id=str(service.id),
                service_type=service.service_type,
                catalog_service_id=str(service.catalog_service_id)
                if service.catalog_service_id
                else None,
                expires_at=service.expire_at,
            )
        )
        return saved

    async def renew_due_catalog_services(
        self,
        now: datetime | None = None,
        limit: int = 100,
    ) -> SHMAutoRenewalResult:
        """Автоматически продлить истёкшие SHM-услуги с auto_bill."""
        cutoff = now or datetime.now(UTC)
        due_services = await self._service_repo.get_expiring_auto_bill(
            cutoff=cutoff,
            limit=limit,
        )
        result = SHMAutoRenewalResult(
            processed=0,
            renewed=0,
            suspended=0,
            failed=0,
            errors=[],
        )

        for service in due_services:
            result["processed"] += 1
            try:
                await self.renew_catalog_service(
                    service_id=service.id,
                    now=cutoff,
                )
                result["renewed"] += 1
            except ValueError as exc:
                if service.status == ServiceStatus.SUSPENDED:
                    result["suspended"] += 1
                else:
                    result["failed"] += 1
                result["errors"].append(
                    {
                        "service_id": str(service.id),
                        "error": str(exc),
                    }
                )

        return result

    async def stop_catalog_service(
        self,
        service_id: UUID,
        stopped_at: datetime | None = None,
        reason: str = "user_request",
    ) -> UserService:
        """Остановить SHM-услугу и вернуть неиспользованный остаток периода."""
        service = await self._service_repo.get(service_id)
        if service is None:
            raise ValueError(f"Service {service_id} not found")
        if service.activated_at is None or service.expire_at is None:
            return await self.deactivate_service(service_id=service_id, reason=reason)

        abonent = await self._service_repo.get_abonent(service.abonent_id)
        if abonent is None:
            raise ValueError(f"Abonent {service.abonent_id} not found")

        refund = self._billing_engine.calculate_shm_refund(
            cost=Money(service.cost, service.currency),
            starts_at=service.activated_at,
            ends_at=service.expire_at,
            stopped_at=stopped_at or datetime.now(UTC),
            mode=SHMBillingMode.FIXED_30_DAYS,
        )
        if not refund.refund.is_zero():
            abonent.change_balance(refund.refund, reason="shm_service_refund")
            await self._service_repo.save_abonent(abonent)

        service.deactivate(reason=reason)
        saved = await self._service_repo.save(service)

        from app.core.domain.events.service_events import ServiceDeactivatedEvent

        await self._event_bus.publish(
            ServiceDeactivatedEvent(
                abonent_id=str(service.abonent_id),
                service_id=str(service_id),
                service_type=service.service_type,
                catalog_service_id=str(service.catalog_service_id)
                if service.catalog_service_id
                else None,
                reason=reason,
            )
        )
        return saved

    async def deactivate_service(
        self,
        service_id: UUID,
        reason: str = "",
    ) -> UserService | None:
        """
        Деактивировать услугу.

        Args:
            service_id: ID услуги
            reason: Причина деактивации

        Returns:
            UserService | None: Обновлённая услуга или None
        """
        service = await self._service_repo.get(service_id)

        if service is None:
            return None

        service.deactivate(reason=reason)

        saved = await self._service_repo.save(service)

        # Публикуем событие
        from app.core.domain.events.service_events import ServiceDeactivatedEvent

        event = ServiceDeactivatedEvent(
            abonent_id=str(service.abonent_id),
            service_id=str(service_id),
            service_type=service.service_type,
            reason=reason,
        )
        await self._event_bus.publish(event)

        logger.info(
            "Service deactivated",
            service_id=service_id,
            reason=reason,
        )

        return saved

    async def get_services(
        self,
        abonent_id: UUID,
        active_only: bool = True,
    ) -> list[UserService]:
        """Получить услуги абонента."""
        return await self._service_repo.get_by_abonent(
            abonent_id=abonent_id,
            active_only=active_only,
        )

    async def get_service(self, service_id: UUID) -> UserService | None:
        """Получить услугу по ID."""
        return await self._service_repo.get(service_id)

    async def _get_catalog_service(self, service_id: UUID) -> CatalogService:
        if self._catalog_service_repo is None:
            raise RuntimeError("Catalog service repository is not configured")
        catalog = await self._catalog_service_repo.get(service_id)
        if catalog is None:
            raise ValueError(f"Catalog service {service_id} not found")
        return catalog

    async def _ensure_catalog_service_limit(
        self,
        abonent_id: UUID,
        catalog: CatalogService,
        quantity: int,
    ) -> None:
        if catalog.max_count is None:
            return
        if quantity > catalog.max_count:
            raise ValueError(
                f"Catalog service {catalog.id} max_count exceeded"
            )

        active_services = await self._service_repo.get_by_abonent(
            abonent_id=abonent_id,
            active_only=True,
        )
        active_count = sum(
            1
            for service in active_services
            if service.catalog_service_id == catalog.id
        )
        if active_count >= catalog.max_count:
            raise ValueError(
                f"Catalog service {catalog.id} max_count exceeded"
            )

    def _build_user_service(
        self,
        abonent_id: UUID,
        catalog: CatalogService,
        quantity: int,
        starts_at: datetime,
        expire_at: datetime,
        paid_amount: Money,
        parent_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> UserService:
        return UserService(
            abonent_id=abonent_id,
            service_type=catalog.category or catalog.name,
            catalog_service_id=catalog.id,
            status=ServiceStatus.INIT,
            activated_at=starts_at,
            expire_at=expire_at,
            cost=float(paid_amount.amount),
            currency=paid_amount.currency.value,
            period_cost=catalog.period_cost,
            next_service_id=catalog.next_service_id,
            parent_id=parent_id,
            quantity=quantity,
            auto_bill=True,
            pay_always=catalog.pay_always,
            pay_in_credit=catalog.pay_in_credit,
            no_discount=catalog.no_discount,
            metadata=metadata,
        )
