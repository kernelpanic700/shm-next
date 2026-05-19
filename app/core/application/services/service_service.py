# =============================================================================
# shm-next — Service Application Service
# =============================================================================
"""
Application Service для управления услугами абонентов.
"""

from __future__ import annotations

from uuid import UUID

import structlog

from app.core.domain.entities.service import UserService
from app.core.domain.repositories.service import ServiceRepositoryProtocol
from app.core.services.event_bus import EventBus

logger = structlog.get_logger("service_service")


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
    ) -> None:
        self._service_repo = service_repo
        self._event_bus = event_bus

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
