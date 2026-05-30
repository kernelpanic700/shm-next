# =============================================================================
# shm-next — API v1: Events
# =============================================================================
"""Эндпоинты для работы с событиями и аудитом."""

from __future__ import annotations

from datetime import datetime

from litestar import Controller, get
from litestar.datastructures import State

from app.api.dto.responses import ApiResponse, AuditLogResponse
from app.infrastructure.db.models import AuditLogModel


class EventsController(Controller):
    path = "/events"
    tags = ["Events"]

    @get(
        "/",
        summary="Список событий",
        description="Получить список аудиторских событий",
    )
    async def list_events(
        self,
        state: State,
        action: str | None = None,
        resource_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> ApiResponse:
        from sqlalchemy import and_, select
        from sqlalchemy.ext.asyncio import AsyncSession

        session: AsyncSession = state.session
        stmt = select(AuditLogModel).order_by(AuditLogModel.created_at.desc())

        filters = []
        if action:
            filters.append(AuditLogModel.action == action)
        if resource_type:
            filters.append(AuditLogModel.resource_type == resource_type)
        if from_date:
            filters.append(AuditLogModel.created_at >= from_date)
        if to_date:
            filters.append(AuditLogModel.created_at <= to_date)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        result = await session.execute(stmt)
        logs = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "items": [
                    AuditLogResponse(
                        id=log.id,
                        actor_id=log.actor_id,
                        action=log.action,
                        resource_type=log.resource_type,
                        resource_id=log.resource_id,
                        old_values=log.old_values,
                        new_values=log.new_values,
                        created_at=log.created_at or datetime.now(),
                    ).model_dump()
                    for log in logs
                ],
                "total": len(logs),
                "page": page,
                "per_page": per_page,
            },
        )

    @get(
        "/types",
        summary="Типы событий",
        description="Получить список доступных типов событий",
    )
    async def get_event_types(self) -> ApiResponse:
        from app.core.domain.value_objects.event_type import EventType

        return ApiResponse(
            success=True,
            data={
                "types": [
                    {"value": e.value, "category": e.category(), "critical": e.is_critical()}
                    for e in EventType
                ]
            },
        )
