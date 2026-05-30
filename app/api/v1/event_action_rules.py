# =============================================================================
# shm-next - API v1: Event Action Rules
# =============================================================================
from __future__ import annotations

from uuid import UUID

from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND

from app.api.dependencies import provide_uow_dependency
from app.api.dto.requests import (
    EventActionRuleCreateRequest,
    EventActionRuleUpdateRequest,
)
from app.api.dto.responses import (
    EventActionRuleListResponse,
    EventActionRuleResponse,
)
from app.core.domain.entities.event_action_rule import EventActionRule
from app.infrastructure.db.unit_of_work import UnitOfWork


class EventActionRuleController(Controller):
    """Контроллер правил действий по событиям SHM."""

    path = "/event-action-rules"
    tags = ["SHM Event Actions"]
    dependencies = {"uow": Provide(provide_uow_dependency)}

    @get("/", summary="Список правил действий по событиям")
    async def list_rules(
        self,
        uow: UnitOfWork,
        event_type: str | None = None,
        enabled_only: bool = False,
    ) -> EventActionRuleListResponse:
        rules = await uow.event_action_rules.list(
            event_type=event_type,
            enabled_only=enabled_only,
        )
        return EventActionRuleListResponse(
            items=[EventActionRuleResponse.model_validate(rule) for rule in rules],
            total=len(rules),
        )

    @get("/{rule_id:uuid}", summary="Получить правило действия")
    async def get_rule(
        self,
        rule_id: UUID,
        uow: UnitOfWork,
    ) -> EventActionRuleResponse:
        rule = await uow.event_action_rules.get(rule_id)
        if rule is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Event action rule {rule_id} not found",
            )
        return EventActionRuleResponse.model_validate(rule)

    @post("/", summary="Создать правило действия", status_code=HTTP_201_CREATED)
    async def create_rule(
        self,
        data: EventActionRuleCreateRequest,
        uow: UnitOfWork,
    ) -> EventActionRuleResponse:
        rule = EventActionRule(
            event_type=data.event_type,
            action_type=data.action_type,
            title=data.title,
            service_type=data.service_type,
            catalog_service_id=data.catalog_service_id,
            server_group_id=data.server_group_id,
            server_id=data.server_id,
            template_id=data.template_id,
            command=data.command,
            settings=data.settings,
            priority=data.priority,
            max_retries=data.max_retries,
            is_enabled=data.is_enabled,
        )
        saved = await uow.event_action_rules.save(rule)
        await uow.commit()
        return EventActionRuleResponse.model_validate(saved)

    @patch("/{rule_id:uuid}", summary="Обновить правило действия")
    async def update_rule(
        self,
        rule_id: UUID,
        data: EventActionRuleUpdateRequest,
        uow: UnitOfWork,
    ) -> EventActionRuleResponse:
        existing = await uow.event_action_rules.get(rule_id)
        if existing is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Event action rule {rule_id} not found",
            )

        rule = EventActionRule(
            id=existing.id,
            event_type=data.event_type if data.event_type is not None else existing.event_type,
            action_type=data.action_type if data.action_type is not None else existing.action_type,
            title=data.title if data.title is not None else existing.title,
            service_type=data.service_type if data.service_type is not None else existing.service_type,
            catalog_service_id=data.catalog_service_id if data.catalog_service_id is not None else existing.catalog_service_id,
            server_group_id=data.server_group_id if data.server_group_id is not None else existing.server_group_id,
            server_id=data.server_id if data.server_id is not None else existing.server_id,
            template_id=data.template_id if data.template_id is not None else existing.template_id,
            command=data.command if data.command is not None else existing.command,
            settings=data.settings if data.settings is not None else existing.settings,
            priority=data.priority if data.priority is not None else existing.priority,
            max_retries=data.max_retries if data.max_retries is not None else existing.max_retries,
            is_enabled=data.is_enabled if data.is_enabled is not None else existing.is_enabled,
            created_at=existing.created_at,
            version=existing.version + 1,
        )
        saved = await uow.event_action_rules.save(rule)
        await uow.commit()
        return EventActionRuleResponse.model_validate(saved)

    @delete("/{rule_id:uuid}", summary="Отключить правило действия", status_code=HTTP_204_NO_CONTENT)
    async def disable_rule(
        self,
        rule_id: UUID,
        uow: UnitOfWork,
    ) -> None:
        rule = await uow.event_action_rules.get(rule_id)
        if rule is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Event action rule {rule_id} not found",
            )
        rule.disable()
        await uow.event_action_rules.save(rule)
        await uow.commit()
