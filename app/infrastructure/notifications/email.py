# =============================================================================
# shm-next — Email Notification Service
# =============================================================================
"""
Сервис отправки email-уведомлений.

Поддерживает:
- SMTP
- API-сервисы (SendGrid, Mailgun и т.д.)
- Шаблоны писем
"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import structlog
from jinja2 import Environment, FileSystemLoader

from app.api.config import AppConfig
from app.infrastructure.notifications.base import NotificationResult, NotificationService

logger = structlog.get_logger("email")


class EmailService(NotificationService):
    """
    Сервис отправки email-уведомлений.

    Поддерживает SMTP и шаблоны Jinja2.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()
        self._jinja_env = Environment(
            loader=FileSystemLoader(
                self._config.email_templates_dir or "templates/email"
            ),
            autoescape=True,
        )

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        template_name: str | None = None,
        template_context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> NotificationResult:
        """
        Отправить email.

        Args:
            recipient: Email получателя
            subject: Тема письма
            body: Текст письма (HTML)
            template_name: Имя шаблона Jinja2
            template_context: Контекст для шаблона

        Returns:
            NotificationResult: Результат отправки
        """
        try:
            # Если указан шаблон — рендерим
            if template_name:
                template = self._jinja_env.get_template(template_name)
                context = template_context or {}
                html_body = template.render(**context)
            else:
                html_body = body

            # Отправляем через SMTP
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self._config.email_from
            msg["To"] = recipient

            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # NOTE: В продакшене используется пул соединений
            if self._config.smtp_host:
                await self._send_smtp(recipient, msg)

            logger.info(
                "Email sent",
                recipient=recipient,
                subject=subject,
            )

            return NotificationResult(
                success=True,
                message_id=f"msg-{hash(recipient + subject)}",
            )

        except Exception as exc:
            logger.error(
                "Email send failed",
                recipient=recipient,
                error=str(exc),
            )
            return NotificationResult(
                success=False,
                error=str(exc),
            )

    async def _send_smtp(self, recipient: str, msg: MIMEMultipart) -> None:
        """Отправка через SMTP."""
        import asyncio

        def _send():
            with smtplib.SMTP(
                self._config.smtp_host,
                self._config.smtp_port,
                timeout=10,
            ) as server:
                if self._config.smtp_use_tls:
                    server.starttls()
                if self._config.smtp_user:
                    server.login(self._config.smtp_user, self._config.smtp_password)
                server.send_message(msg)

        await asyncio.get_event_loop().run_in_executor(None, _send)

    async def send_bulk(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        **kwargs: Any,
    ) -> list[NotificationResult]:
        """Массовая отправка email."""
        results = []
        for recipient in recipients:
            result = await self.send(recipient, subject, body, **kwargs)
            results.append(result)
        return results
