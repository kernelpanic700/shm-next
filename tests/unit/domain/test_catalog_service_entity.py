from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.domain.entities import CatalogService
from app.core.domain.value_objects import Money


def test_catalog_service_matches_shm_defaults() -> None:
    service = CatalogService(name="Internet 100M", cost=Money("500.00"))

    assert service.name == "Internet 100M"
    assert service.cost == Money("500.00")
    assert service.period_cost == Decimal("1.0000")
    assert service.allow_to_order is True
    assert service.pay_always is False
    assert service.pay_in_credit is False
    assert service.no_discount is False
    assert service.is_composite is False
    assert service.is_deleted is False


def test_catalog_service_tracks_composite_children() -> None:
    first_child = uuid4()
    second_child = uuid4()
    service = CatalogService(name="Bundle", cost=Money("700.00"))

    service.set_children([first_child, second_child])

    assert service.children == [first_child, second_child]
    assert service.is_composite is True
    assert service.version == 2


def test_catalog_service_delete_disables_ordering() -> None:
    service = CatalogService(name="Legacy", cost=Money("100.00"))

    service.mark_deleted()

    assert service.is_deleted is True
    assert service.allow_to_order is False


def test_catalog_service_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="name"):
        CatalogService(name=" ")

    with pytest.raises(ValueError, match="cost"):
        CatalogService(name="Broken", cost=Money("-1.00"))

    with pytest.raises(ValueError, match="max_count"):
        CatalogService(name="Broken", max_count=0)
