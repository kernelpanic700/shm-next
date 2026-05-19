# =============================================================================
# shm-next — Unit Tests: Repository Protocols
# =============================================================================
"""Тесты для протоколов репозиториев доменного слоя."""

from __future__ import annotations

import pytest

from app.core.domain.repositories import (
    AbonentRepositoryProtocol,
    BaseRepository,
    BillingRepositoryProtocol,
    BonusEntryRepositoryProtocol,
    DiscountRepositoryProtocol,
    InvoiceRepositoryProtocol,
    PaymentRepositoryProtocol,
    ServiceRepositoryProtocol,
    SessionRepositoryProtocol,
    SpoolRepositoryProtocol,
    TariffRepositoryProtocol,
    TariffServiceRepositoryProtocol,
    WithdrawRepositoryProtocol,
)


class TestBaseRepositoryProtocol:
    """Тесты BaseRepository protocol."""

    def test_protocol_defined(self):
        assert issubclass(BaseRepository, object)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseRepository()  # type: ignore


class TestAbonentRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(AbonentRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_phone", "get_by_account", "list", "save", "delete", "exists"]
        for method in required:
            assert hasattr(AbonentRepositoryProtocol, method)


class TestTariffRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(TariffRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_name", "list", "save", "get_services_for_tariff"]
        for method in required:
            assert hasattr(TariffRepositoryProtocol, method)


class TestPaymentRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(PaymentRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["create", "get", "get_by_abonent", "confirm", "refund"]
        for method in required:
            assert hasattr(PaymentRepositoryProtocol, method)


class TestWithdrawRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(WithdrawRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_abonent", "get_pending", "get_by_service", "save"]
        for method in required:
            assert hasattr(WithdrawRepositoryProtocol, method)


class TestServiceRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(ServiceRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_abonent", "get_active_by_abonent", "save"]
        for method in required:
            assert hasattr(ServiceRepositoryProtocol, method)


class TestBillingRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(BillingRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = [
            "get_abonent_balance",
            "get_abonent_services",
            "create_withdraw",
            "get_abonent_tariff",
            "get_abonent_last_payment",
        ]
        for method in required:
            assert hasattr(BillingRepositoryProtocol, method)


class TestSpoolRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(SpoolRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = [
            "create_task",
            "get_pending",
            "mark_processing",
            "mark_completed",
            "mark_failed",
            "move_to_dlq",
        ]
        for method in required:
            assert hasattr(SpoolRepositoryProtocol, method)


class TestDiscountRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(DiscountRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_active", "get_valid_at", "save"]
        for method in required:
            assert hasattr(DiscountRepositoryProtocol, method)


class TestBonusEntryRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(BonusEntryRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_abonent", "get_active", "get_expired", "save"]
        for method in required:
            assert hasattr(BonusEntryRepositoryProtocol, method)


class TestSessionRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(SessionRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_token_hash", "get_active_by_abonent", "cleanup_expired", "save"]
        for method in required:
            assert hasattr(SessionRepositoryProtocol, method)


class TestInvoiceRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(InvoiceRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_abonent", "get_unpaid", "get_overdue", "save"]
        for method in required:
            assert hasattr(InvoiceRepositoryProtocol, method)


class TestTariffServiceRepositoryProtocol:
    def test_protocol_defined(self):
        assert issubclass(TariffServiceRepositoryProtocol, object)

    def test_has_required_methods(self):
        required = ["get", "get_by_tariff", "get_by_service_type", "save"]
        for method in required:
            assert hasattr(TariffServiceRepositoryProtocol, method)
