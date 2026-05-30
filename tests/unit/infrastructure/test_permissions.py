from uuid import uuid4

from app.infrastructure.auth.permissions import (
    Permission,
    Role,
    has_any_permission,
    has_permission,
    required_permission_for_route,
)


def test_role_permission_matrix_allows_expected_admin_actions() -> None:
    assert has_permission(Role.ADMIN, Permission.ABONENTS_READ)
    assert has_permission(Role.ADMIN, Permission.PAYMENTS_REFUND)
    assert has_permission(Role.SUPER_ADMIN, "anything:anywhere")


def test_role_permission_matrix_keeps_abonent_scoped() -> None:
    assert has_permission(Role.ABONENT, Permission.SELF_READ)
    assert has_permission(Role.ABONENT, Permission.SELF_WRITE)
    assert not has_permission(Role.ABONENT, Permission.BILLING_READ)
    assert not has_permission(Role.ABONENT, Permission.PAYMENTS_READ)
    assert not has_permission(Role.ABONENT, Permission.PAYMENTS_WRITE)
    assert not has_permission(Role.ABONENT, Permission.ABONENTS_READ)


def test_route_policy_allows_self_scoped_billing_without_admin_permission() -> None:
    abonent_id = uuid4()

    assert required_permission_for_route(f"/api/v1/billing/{abonent_id}/balance", "GET", str(abonent_id)) is None


def test_route_policy_requires_permission_for_cross_abonent_billing() -> None:
    assert (
        required_permission_for_route(f"/api/v1/billing/{uuid4()}/balance", "GET", str(uuid4()))
        == Permission.BILLING_READ
    )


def test_route_policy_keeps_payment_admin_actions_separate_from_user_create() -> None:
    payment_id = uuid4()

    assert required_permission_for_route("/api/v1/payments/", "POST", str(uuid4())) is None
    assert required_permission_for_route(f"/api/v1/payments/{payment_id}/confirm", "POST", str(uuid4())) == (
        Permission.PAYMENTS_WRITE
    )
    assert required_permission_for_route(f"/api/v1/payments/{payment_id}/refund", "POST", str(uuid4())) == (
        Permission.PAYMENTS_REFUND
    )


def test_has_any_permission_supports_wildcard_and_explicit_grants() -> None:
    assert has_any_permission(["*"], Permission.CONFIG_WRITE)
    assert has_any_permission([Permission.CONFIG_READ], Permission.CONFIG_READ)
    assert not has_any_permission([Permission.CONFIG_READ], Permission.CONFIG_WRITE)
