# =============================================================================
# shm-next — Webhook Service
# =============================================================================
"""Сервис для отправки исходящих вебхуков."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import structlog

from app.infrastructure.db.unit_of_work import UnitOfWork

logger = structlog.get_logger(__name__)


class WebhookService:
    """Сервис для отправки вебхуков с retry и HMAC-подписью."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _sign_payload(self, payload: dict, secret: str) -> str:
        """HMAC-SHA256 подпись payload."""
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    async def send_webhook(
        self,
        url: str,
        payload: dict[str, Any],
        event_type: str,
        secret: str | None = None,
        max_retries: int = 3,
    ) -> dict:
        """Отправить вебхук с retry-логикой и HMAC-подписью."""
        import httpx

        headers = {"Content-Type": "application/json", "X-Event-Type": event_type}

        if secret:
            headers["X-Signature"] = self._sign_payload(payload, secret)

        async with self.uow:
            webhook_log = await self.uow.webhooks.create({
                "url": url,
                "payload": payload,
                "event_type": event_type,
                "status": "pending",
            })
            await self.uow.commit()

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers, timeout=30.0)

                    async with self.uow:
                        webhook_log.status = "success"
                        webhook_log.response_status = response.status_code
                        webhook_log.response_body = response.text[:500]
                        await self.uow.webhooks.save(webhook_log)
                        await self.uow.commit()

                    logger.info("webhook_sent", url=url, attempt=attempt + 1)
                    return {"status": "success", "status_code": response.status_code}

            except Exception as e:
                logger.warning("webhook_attempt_failed", url=url, attempt=attempt + 1, error=str(e))

                if attempt == max_retries - 1:
                    async with self.uow:
                        webhook_log.status = "failed"
                        webhook_log.error = str(e)
                        await self.uow.webhooks.save(webhook_log)
                        await self.uow.commit()

                    raise

        return {"status": "error", "message": "Max retries exceeded"}
