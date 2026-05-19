# =============================================================================
# shm-next — API v1: Webhooks
# =============================================================================
"""Эндпоинты для управления webhook-уведомлениями."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from litestar import Controller, delete, get, post
from litestar.datastructures import State
from litestar.exceptions import HTTPException

from app.api.dto.requests import WebhookCreate
from app.api.dto.responses import ApiResponse, WebhookResponse


class WebhookController(Controller):
    path = "/v1/webhooks"
    tags = ["Webhooks"]

    @get(
        "/",
        summary="Список webhooks",
        description="Получить список зарегистрированных webhooks",
    )
    async def list_webhooks(
        self,
        state: State,
        is_active: bool | None = None,
    ) -> ApiResponse:
        from sqlalchemy import select

        from app.infrastructure.db.models import Webhook

        session = state.session
        stmt = select(Webhook)

        if is_active is not None:
            stmt = stmt.where(Webhook.is_active == is_active)

        result = await session.execute(stmt)
        webhooks = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "items": [
                    WebhookResponse(
                        id=wh.id,
                        url=wh.url,
                        events=wh.events,
                        is_active=wh.is_active,
                        created_at=wh.created_at or datetime.now(),
                    ).model_dump()
                    for wh in webhooks
                ]
            },
        )

    @post(
        "/",
        summary="Зарегистрировать webhook",
        description="Создать новый webhook для получения уведомлений",
        status_code=201,
    )
    async def create_webhook(
        self,
        data: WebhookCreate,
        state: State,
    ) -> ApiResponse:
        from app.infrastructure.db.models import Webhook

        webhook = Webhook(
            url=data.url,
            events=data.events,
            is_active=data.is_active,
            secret=data.secret,
        )
        state.session.add(webhook)
        await state.session.commit()
        await state.session.refresh(webhook)

        return ApiResponse(
            success=True,
            data=WebhookResponse(
                id=webhook.id,
                url=webhook.url,
                events=webhook.events,
                is_active=webhook.is_active,
                created_at=webhook.created_at or datetime.now(),
            ).model_dump(),
        )

    @delete(
        "/{webhook_id:uuid}",
        summary="Удалить webhook",
        description="Удалить регистрацию webhook",
        status_code=200,
    )
    async def delete_webhook(
        self,
        webhook_id: UUID,
        state: State,
    ) -> ApiResponse:
        from app.infrastructure.db.models import Webhook

        webhook = await state.session.get(Webhook, webhook_id)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

        await state.session.delete(webhook)
        await state.session.commit()

        return ApiResponse(success=True, data={"deleted": True})
