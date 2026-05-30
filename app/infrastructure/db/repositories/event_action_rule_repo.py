# =============================================================================
# shm-next - EventActionRule Repository
# =============================================================================
from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities.event_action_rule import EventActionRule
from app.core.domain.repositories.event_action_rule import (
    EventActionRuleRepositoryProtocol,
)
from app.infrastructure.db.models import EventActionRuleModel


class EventActionRuleRepository(EventActionRuleRepositoryProtocol):
    """Репозиторий правил действий по событиям."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, rule_id: UUID) -> EventActionRule | None:
        model = await self._session.get(EventActionRuleModel, rule_id)
        return self._to_domain(model) if model else None

    async def get_matching(
        self,
        event_type: str,
        service_type: str | None = None,
        catalog_service_id: UUID | None = None,
    ) -> list[EventActionRule]:
        stmt = (
            select(EventActionRuleModel)
            .where(EventActionRuleModel.event_type == event_type)
            .where(EventActionRuleModel.is_enabled.is_(True))
            .where(
                or_(
                    EventActionRuleModel.service_type.is_(None),
                    EventActionRuleModel.service_type == service_type,
                )
            )
            .where(
                or_(
                    EventActionRuleModel.catalog_service_id.is_(None),
                    EventActionRuleModel.catalog_service_id == catalog_service_id,
                )
            )
            .order_by(EventActionRuleModel.priority.desc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list(
        self,
        event_type: str | None = None,
        enabled_only: bool = False,
    ) -> list[EventActionRule]:
        stmt = select(EventActionRuleModel).order_by(
            EventActionRuleModel.event_type,
            EventActionRuleModel.priority.desc(),
            EventActionRuleModel.title,
        )
        if event_type:
            stmt = stmt.where(EventActionRuleModel.event_type == event_type)
        if enabled_only:
            stmt = stmt.where(EventActionRuleModel.is_enabled.is_(True))

        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def save(self, rule: EventActionRule) -> EventActionRule:
        model = await self._session.get(EventActionRuleModel, rule.id)
        if model is None:
            model = EventActionRuleModel(id=rule.id)
            self._session.add(model)

        model.event_type = rule.event_type
        model.action_type = rule.action_type
        model.title = rule.title
        model.service_type = rule.service_type
        model.catalog_service_id = rule.catalog_service_id
        model.settings = rule.settings or None
        model.priority = rule.priority
        model.max_retries = rule.max_retries
        model.is_enabled = rule.is_enabled
        model.version = rule.version

        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    def _to_domain(self, model: EventActionRuleModel) -> EventActionRule:
        return EventActionRule(
            id=model.id,
            event_type=model.event_type,
            action_type=model.action_type,
            title=model.title,
            service_type=model.service_type,
            catalog_service_id=model.catalog_service_id,
            settings=model.settings,
            priority=model.priority,
            max_retries=model.max_retries,
            is_enabled=model.is_enabled,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )
