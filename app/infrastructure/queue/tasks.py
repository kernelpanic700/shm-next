# =============================================================================
# shm-next — Taskiq Tasks
# =============================================================================
"""
Фоновые задачи (Taskiq tasks).

Все тяжёлые и долгие операции выполняются асинхронно
через очередь задач Taskiq.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timezone
from typing import Any

from taskiq import TaskiqBroker
from taskiq_redis import RedisAsyncResultBackend

from app.api.config import AppConfig
from app.core.services.billing_engine import BillingEngine
from app.infrastructure.external.action_registry import ActionRegistry


def create_broker() -> TaskiqBroker:
    """
    Создание Taskiq брокера.

    Returns:
        TaskiqBroker: Настроенный брокер задач
    """
    config = AppConfig()

    broker = TaskiqBroker(
        broker_url=config.taskiq_broker_url,
        result_backend=RedisAsyncResultBackend(result_url=config.taskiq_result_backend),
    )

    # Регистрация встроенных действий
    _register_default_actions(broker)

    return broker


def _register_default_actions(broker: TaskiqBroker) -> None:
    """Регистрация стандартных действий в реестре."""
    registry = ActionRegistry()

    # Пример: отправка уведомлений
    async def send_notification(
        abonent_id: str,
        channel: str,
        message: str,
    ) -> dict:
        """Отправка уведомления абоненту."""
        # Реализация отправки
        return {"status": "sent", "channel": channel}

    # Пример: вызов внешнего API NAS
    async def nas_command(
        command: str,
        params: dict[str, Any],
    ) -> dict:
        """Отправка команды на NAS (BRAS)."""
        # Реализация вызова NAS API
        return {"status": "executed", "command": command}

    # Пример: webhook вызов
    async def send_webhook(
        url: str,
        payload: dict[str, Any],
        secret: str | None = None,
    ) -> dict:
        """Отправка webhook-уведомления."""
        import httpx

        headers = {"Content-Type": "application/json"}
        if secret:
            import hashlib
            import hmac
            import json

            body = json.dumps(payload)
            signature = hmac.new(
                secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature"] = signature

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            return {
                "status_code": response.status_code,
                "body": response.text,
            }

    registry.register("send_notification", send_notification)
    registry.register("nas_command", nas_command)
    registry.register("send_webhook", send_webhook)


# === Scheduled Tasks ===

async def run_billing_cycle() -> dict[str, Any]:
    """
    Биллинг-цикл — периодическая задача расчёта списаний.

    Выполняется ежедневно в полночь.
    """
    from app.infrastructure.db.database import create_engine, create_session_factory
    from app.infrastructure.db.repositories.abonent_repo import AbonentRepository
    from app.infrastructure.db.repositories.service_repo import ServiceRepository
    from app.infrastructure.db.repositories.withdraw_repo import WithdrawRepository

    config = AppConfig()
    engine = create_engine(config.database_url)
    factory = create_session_factory(engine)

    stats = {
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "total_amount": 0.0,
    }

    try:
        async with factory() as session:
            async with session.begin():
                abonent_repo = AbonentRepository(session)
                service_repo = ServiceRepository(session)
                withdraw_repo = WithdrawRepository(session)

                billing_engine = BillingEngine()

                # Получаем активных абонентов
                abonents = await abonent_repo.list(
                    offset=0,
                    limit=config.billing_batch_size,
                    status="ACTIVE",
                )

                for abonent in abonents:
                    try:
                        services = await service_repo.get_by_abonent(
                            abonent.id, active_only=True
                        )

                        for service in services:
                            from app.core.domain.value_objects import Money

                            cost_per_day = Money(
                                service.cost / 30, service.currency
                            )

                            period_start = (
                                service.activated_at.date()
                                if service.activated_at
                                else date.today()
                            )
                            period_end = date.today()

                            amount = billing_engine.calculate_withdraw(
                                cost_per_day=cost_per_day,
                                period_start=period_start,
                                period_end=period_end,
                                strategy="honest",
                            )

                            if float(amount.amount) > 0:
                                await withdraw_repo.create_withdraw(
                                    abonent_id=abonent.id,
                                    service_id=service.id,
                                    amount=float(amount.amount),
                                    currency=amount.currency.code,
                                )

                        stats["processed"] += 1
                        stats["successful"] += 1

                    except Exception:
                        stats["failed"] += 1

        return stats

    finally:
        await engine.dispose()


async def cleanup_expired_sessions() -> int:
    """
    Очистка истёкших сессий.

    Выполняется ежедневно.
    """

    from app.infrastructure.db.database import create_engine, create_session_factory
    from app.infrastructure.db.models import Session

    config = AppConfig()
    engine = create_engine(config.database_url)
    factory = create_session_factory(engine)

    try:
        async with factory() as session:
            async with session.begin():
                from sqlalchemy import select

                now = datetime.now(UTC)
                stmt = select(Session).where(Session.expires_at < now)
                result = await session.execute(stmt)
                expired = result.scalars().all()

                for s in expired:
                    await session.delete(s)

                return len(expired)
    finally:
        await engine.dispose()


async def retry_failed_spool_tasks() -> int:
    """
    Повторная обработка неудачных задач из Spool.

    Выполняется каждые 5 минут.
    """
    from app.core.domain.value_objects import SpoolStatus
    from app.infrastructure.db.database import create_engine, create_session_factory
    from app.infrastructure.db.repositories.spool_repo import SpoolTaskRepository

    config = AppConfig()
    engine = create_engine(config.database_url)
    factory = create_session_factory(engine)

    retried = 0

    try:
        async with factory() as session:
            async with session.begin():
                repo = SpoolTaskRepository(session)

                # Получаем задачи в статусе FAILED
                tasks = await repo.get_pending(
                    action_types=None,
                    limit=50,
                )

                for task in tasks:
                    if task.get("status") == SpoolStatus.FAILED.value:
                        # Сбрасываем статус для повтора
                        await repo.mark_processing(
                            task["id"], worker_id="retry-worker"
                        )
                        retried += 1

        return retried
    finally:
        await engine.dispose()


async def send_pending_notifications() -> int:
    """
    Отправка ожидающих уведомлений.

    Выполняется каждую минуту.
    """
    from app.infrastructure.db.database import create_engine, create_session_factory
    from app.infrastructure.db.models import Notification
    from app.infrastructure.notifications.email import EmailService
    from app.infrastructure.notifications.sms import SMSService

    config = AppConfig()
    engine = create_engine(config.database_url)
    factory = create_session_factory(engine)

    sent = 0

    try:
        async with factory() as session:
            async with session.begin():
                from sqlalchemy import and_, select

                stmt = select(Notification).where(
                    and_(
                        Notification.status == "PENDING",
                        Notification.sent_at.is_(None),
                    )
                ).limit(100)

                result = await session.execute(stmt)
                notifications = result.scalars().all()

                email_service = EmailService(config)
                sms_service = SMSService(config)

                for notification in notifications:
                    try:
                        if notification.channel == "email":
                            success = await email_service.send_simple(
                                to="",  # Would be filled from abonent data
                                subject=notification.subject or "",
                                html=notification.body,
                            )
                        elif notification.channel == "sms":
                            result_sms = await sms_service.send(
                                phone="",  # Would be filled from abonent data
                                message=notification.body,
                            )
                            success = result_sms.get("success", False)
                        else:
                            success = False

                        if success:
                            notification.status = "SENT"
                            notification.sent_at = datetime.now(timezone.utc)
                        else:
                            notification.status = "FAILED"

                        sent += 1

                    except Exception:
                        notification.status = "FAILED"

        return sent
    finally:
        await engine.dispose()
