from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.application.events import ServiceEventSpoolHandler
from app.core.domain.entities import EventActionRule
from app.core.domain.events.abonent_events import AbonentBlockedEvent
from app.core.domain.events.service_events import (
    ServiceActivatedEvent,
    ServiceRenewedEvent,
)


@pytest.mark.asyncio
async def test_service_spool_handler_creates_task_for_matching_rule() -> None:
    rule_repo = AsyncMock()
    spool_repo = AsyncMock()
    handler = ServiceEventSpoolHandler(rule_repo, spool_repo)
    catalog_id = uuid4()
    rule_repo.get_matching.return_value = [
        EventActionRule(
            event_type="service.activated",
            action_type="nas_command",
            service_type="internet",
            settings={"command": "activate"},
            priority=90,
            max_retries=5,
        )
    ]
    spool_repo.create_task.return_value = 42
    event = ServiceActivatedEvent(
        abonent_id=str(uuid4()),
        service_id=str(uuid4()),
        service_type="internet",
        catalog_service_id=str(catalog_id),
        expires_at=datetime(2026, 6, 26, tzinfo=UTC),
        payload={"ip": "10.0.0.10"},
    )

    task_ids = await handler(event)

    assert task_ids == [42]
    rule_repo.get_matching.assert_called_once()
    _, kwargs = spool_repo.create_task.call_args
    assert kwargs["action_type"] == "nas_command"
    assert kwargs["priority"] == 90
    assert kwargs["max_retries"] == 5
    assert kwargs["payload"]["service_type"] == "internet"
    assert kwargs["payload"]["catalog_service_id"] == str(catalog_id)
    assert kwargs["payload"]["settings"] == {"command": "activate"}
    assert kwargs["payload"]["ip"] == "10.0.0.10"


@pytest.mark.asyncio
async def test_service_spool_handler_creates_task_for_abonent_event() -> None:
    rule_repo = AsyncMock()
    spool_repo = AsyncMock()
    handler = ServiceEventSpoolHandler(rule_repo, spool_repo)
    rule_repo.get_matching.return_value = [
        EventActionRule(
            event_type="abonent.blocked",
            action_type="ssh.exec",
            command="block {abonent_id}",
            priority=80,
            max_retries=2,
        )
    ]
    spool_repo.create_task.return_value = 77
    abonent_id = str(uuid4())

    task_ids = await handler(
        AbonentBlockedEvent(
            abonent_id=abonent_id,
            reason="manual",
        )
    )

    assert task_ids == [77]
    rule_repo.get_matching.assert_called_once_with(
        event_type="abonent.blocked",
        service_type=None,
        catalog_service_id=None,
    )
    _, kwargs = spool_repo.create_task.call_args
    assert kwargs["action_type"] == "ssh.exec"
    assert kwargs["payload"]["abonent_id"] == abonent_id
    assert kwargs["payload"]["status"] == "BLOCKED"
    assert kwargs["payload"]["reason"] == "manual"
    assert kwargs["payload"]["rule"]["settings"]["command"] == "block {abonent_id}"


@pytest.mark.asyncio
async def test_service_spool_handler_ignores_events_without_rules() -> None:
    rule_repo = AsyncMock()
    spool_repo = AsyncMock()
    handler = ServiceEventSpoolHandler(rule_repo, spool_repo)
    rule_repo.get_matching.return_value = []

    task_ids = await handler(
        ServiceRenewedEvent(
            abonent_id=str(uuid4()),
            service_id=str(uuid4()),
            service_type="internet",
        )
    )

    assert task_ids == []
    spool_repo.create_task.assert_not_called()
