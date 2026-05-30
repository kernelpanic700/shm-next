# =============================================================================
# shm-next - EventActionRule Repository Protocol
# =============================================================================
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.entities.event_action_rule import EventActionRule


class EventActionRuleRepositoryProtocol(ABC):
    """Протокол репозитория правил действий по событиям."""

    @abstractmethod
    async def get(self, rule_id: UUID) -> EventActionRule | None:
        ...

    @abstractmethod
    async def get_matching(
        self,
        event_type: str,
        service_type: str | None = None,
        catalog_service_id: UUID | None = None,
    ) -> list[EventActionRule]:
        ...

    @abstractmethod
    async def list(
        self,
        event_type: str | None = None,
        enabled_only: bool = False,
    ) -> list[EventActionRule]:
        ...

    @abstractmethod
    async def save(self, rule: EventActionRule) -> EventActionRule:
        ...
