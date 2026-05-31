# =============================================================================
# shm-next - Service Event Spool Handler
# =============================================================================
from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.domain.events.event import DomainEvent
from app.core.domain.repositories.event_action_rule import (
    EventActionRuleRepositoryProtocol,
)
from app.core.domain.repositories.spool import SpoolRepositoryProtocol
from app.core.domain.value_objects.event_type import EventType


class ServiceEventSpoolHandler:
    """Создает spool-задачи для SHM-событий услуг и абонентов."""

    SUPPORTED_EVENTS = {
        EventType.ABONENT_CREATED.value,
        EventType.ABONENT_UPDATED.value,
        EventType.ABONENT_DELETED.value,
        EventType.ABONENT_BLOCKED.value,
        EventType.ABONENT_ACTIVATED.value,
        EventType.ABONENT_DEACTIVATED.value,
        EventType.SERVICE_ACTIVATED.value,
        EventType.SERVICE_DEACTIVATED.value,
        EventType.SERVICE_RENEWED.value,
    }

    def __init__(
        self,
        rule_repo: EventActionRuleRepositoryProtocol,
        spool_repo: SpoolRepositoryProtocol,
    ) -> None:
        self._rule_repo = rule_repo
        self._spool_repo = spool_repo

    async def __call__(self, event: DomainEvent) -> list[int]:
        event_type = event.event_type.value
        if event_type not in self.SUPPORTED_EVENTS:
            return []

        service_type = getattr(event, "service_type", None)
        catalog_service_id = self._parse_uuid(
            getattr(event, "catalog_service_id", None)
        )
        rules = await self._rule_repo.get_matching(
            event_type=event_type,
            service_type=service_type,
            catalog_service_id=catalog_service_id,
        )

        task_ids: list[int] = []
        for rule in rules:
            settings = {
                **rule.settings,
                "rule_id": str(rule.id),
            }
            if rule.server_group_id:
                settings["server_group_id"] = str(rule.server_group_id)
            if rule.server_id:
                settings["server_id"] = str(rule.server_id)
            if rule.template_id:
                settings["template_id"] = str(rule.template_id)
            if rule.command:
                settings["command"] = rule.command

            payload = self._build_payload(
                event,
                settings,
                rule.settings,
            )
            task_id = await self._spool_repo.create_task(
                action_type=rule.action_type,
                payload=payload,
                priority=rule.priority,
                max_retries=rule.max_retries,
            )
            task_ids.append(int(task_id))
        return task_ids

    def _build_payload(
        self,
        event: DomainEvent,
        settings: dict,
        legacy_settings: dict | None = None,
    ) -> dict[str, Any]:
        expires_at = getattr(event, "expires_at", None)
        payload = {
            "settings": legacy_settings if legacy_settings is not None else settings,
            "rule": {
                "settings": settings,
            },
            "event": {
                "id": event.event_id,
                "type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "correlation_id": event.correlation_id,
            },
            "abonent_id": getattr(event, "abonent_id", None),
            "service_id": getattr(event, "service_id", None),
            "service_type": getattr(event, "service_type", None),
            "catalog_service_id": getattr(event, "catalog_service_id", None),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "reason": getattr(event, "reason", None),
            "changes": getattr(event, "changes", None),
            "status": getattr(event, "status", None),
        }
        payload.update(getattr(event, "payload", {}) or {})
        return payload

    def _parse_uuid(self, value: str | UUID | None) -> UUID | None:
        if value is None or isinstance(value, UUID):
            return value
        return UUID(value)
