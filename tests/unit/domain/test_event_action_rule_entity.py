from uuid import uuid4

import pytest

from app.core.domain.entities import EventActionRule


def test_event_action_rule_matches_global_rule() -> None:
    rule = EventActionRule(
        event_type="service.activated",
        action_type="nas_command",
    )

    assert rule.matches("service.activated", service_type="internet")
    assert not rule.matches("service.deactivated", service_type="internet")


def test_event_action_rule_matches_service_type_and_catalog() -> None:
    catalog_id = uuid4()
    rule = EventActionRule(
        event_type="service.activated",
        action_type="nas_command",
        service_type="internet",
        catalog_service_id=catalog_id,
    )

    assert rule.matches("service.activated", "internet", catalog_id)
    assert not rule.matches("service.activated", "voice", catalog_id)
    assert not rule.matches("service.activated", "internet", uuid4())


def test_event_action_rule_disable_prevents_match() -> None:
    rule = EventActionRule(
        event_type="service.activated",
        action_type="nas_command",
    )

    rule.disable()

    assert not rule.matches("service.activated")
    assert rule.version == 2


def test_event_action_rule_validation() -> None:
    with pytest.raises(ValueError, match="event_type"):
        EventActionRule(event_type="", action_type="nas_command")

    with pytest.raises(ValueError, match="action_type"):
        EventActionRule(event_type="service.activated", action_type="")

    with pytest.raises(ValueError, match="priority"):
        EventActionRule(
            event_type="service.activated",
            action_type="nas_command",
            priority=-1,
        )
