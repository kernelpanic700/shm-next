from decimal import Decimal
from uuid import uuid4

from app.api.dto.requests import (
    CatalogServiceCreateRequest,
    CatalogServiceOrderRequest,
    EventActionRuleCreateRequest,
)
from app.api.dto.responses import (
    CatalogServiceResponse,
    EventActionRuleResponse,
)
from app.core.domain.entities import CatalogService, EventActionRule
from app.core.domain.value_objects import Money


def test_catalog_service_create_request_defaults() -> None:
    request = CatalogServiceCreateRequest(name="Internet", cost=Decimal("500.00"))

    assert request.currency == "RUB"
    assert request.period_cost == Decimal("1.0000")
    assert request.allow_to_order is True
    assert request.children == []


def test_catalog_service_order_request() -> None:
    abonent_id = uuid4()
    request = CatalogServiceOrderRequest(
        abonent_id=abonent_id,
        quantity=2,
        bonus_balance=Decimal("50.00"),
    )

    assert request.abonent_id == abonent_id
    assert request.quantity == 2
    assert request.bonus_balance == Decimal("50.00")


def test_catalog_service_response_from_domain() -> None:
    child_id = uuid4()
    service = CatalogService(
        name="Internet",
        cost=Money("500.00"),
        category="internet",
        children=[child_id],
        pay_in_credit=True,
    )

    response = CatalogServiceResponse.model_validate(service)

    assert response.name == "Internet"
    assert response.cost == 500.0
    assert response.category == "internet"
    assert response.children == [child_id]
    assert response.pay_in_credit is True


def test_event_action_rule_request_and_response_from_domain() -> None:
    catalog_id = uuid4()
    request = EventActionRuleCreateRequest(
        event_type="service.activated",
        action_type="nas_command",
        service_type="internet",
        catalog_service_id=catalog_id,
        settings={"command": "activate"},
    )
    rule = EventActionRule(
        event_type=request.event_type,
        action_type=request.action_type,
        service_type=request.service_type,
        catalog_service_id=request.catalog_service_id,
        settings=request.settings,
    )

    response = EventActionRuleResponse.model_validate(rule)

    assert response.event_type == "service.activated"
    assert response.action_type == "nas_command"
    assert response.catalog_service_id == catalog_id
    assert response.settings == {"command": "activate"}
