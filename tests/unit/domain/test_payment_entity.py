# =============================================================================
# shm-next — Payment Entity Tests
# =============================================================================
"""Тесты для сущности Payment."""

from __future__ import annotations

from uuid import uuid4

from app.core.domain.entities.payment import Payment, PaymentStatus


class TestPaymentCreation:
    """Тесты создания платежа."""

    def test_create_minimal(self):
        """Создание с минимальными параметрами."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=100.0,
            currency="RUB",
            payment_method="cash",
        )

        assert payment.id is not None
        assert payment.abonent_id is not None
        assert payment.amount == 100.0
        assert payment.currency == "RUB"
        assert payment.payment_method == "cash"
        assert payment.status == PaymentStatus.NEW
        assert payment.external_id is None
        assert payment.completed_at is None
        assert payment.version == 1

    def test_create_with_external_id(self):
        """Создание с внешним ID."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=500.0,
            currency="USD",
            payment_method="card",
            external_id="pay_12345",
        )

        assert payment.external_id == "pay_12345"

    def test_create_with_metadata(self):
        """Создание с метаданными."""
        meta = {"order_id": "ORD-001", "source": "web"}
        payment = Payment(
            abonent_id=uuid4(),
            amount=200.0,
            currency="RUB",
            payment_method="cash",
            metadata=meta,
        )

        assert payment.metadata == meta

    def test_custom_id(self):
        """Создание с указанным ID."""
        custom_id = uuid4()
        payment = Payment(
            id=custom_id,
            abonent_id=uuid4(),
            amount=100.0,
            currency="RUB",
            payment_method="cash",
        )

        assert payment.id == custom_id


class TestPaymentStatusTransitions:
    """Тесты переходов статуса платежа."""

    def test_confirm(self):
        """Подтверждение платежа."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=100.0,
            currency="RUB",
            payment_method="cash",
        )

        assert payment.status == PaymentStatus.NEW

        payment.confirm()

        assert payment.status == PaymentStatus.COMPLETED
        assert payment.completed_at is not None
        assert payment.version == 2

    def test_refund(self):
        """Возврат платежа."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=100.0,
            currency="RUB",
            payment_method="card",
        )
        payment.confirm()

        payment.refund()

        assert payment.status == PaymentStatus.REFUNDED
        assert payment.version == 3

    def test_fail(self):
        """Отметка как неудачный."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=100.0,
            currency="RUB",
            payment_method="card",
        )

        payment.fail(reason="Insufficient funds")

        assert payment.status == PaymentStatus.FAILED
        assert payment.metadata.get("error") == "Insufficient funds"
        assert payment.version == 2

    def test_fail_without_reason(self):
        """Отметка как неудачный без причины."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=100.0,
            currency="RUB",
            payment_method="cash",
        )

        payment.fail()

        assert payment.status == PaymentStatus.FAILED
        assert payment.metadata.get("error") is None


class TestPaymentStatusFlow:
    """Тесты полного жизненного цикла платежа."""

    def test_full_lifecycle(self):
        """Полный цикл: создание -> подтверждение."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=500.0,
            currency="RUB",
            payment_method="card",
            external_id="ext_001",
        )

        assert payment.status == PaymentStatus.NEW
        assert payment.version == 1

        payment.confirm()

        assert payment.status == PaymentStatus.COMPLETED
        assert payment.completed_at is not None
        assert payment.version == 2

    def test_lifecycle_with_refund(self):
        """Полный цикл: создание -> подтверждение -> возврат."""
        payment = Payment(
            abonent_id=uuid4(),
            amount=300.0,
            currency="RUB",
            payment_method="card",
        )

        payment.confirm()
        payment.refund()

        assert payment.status == PaymentStatus.REFUNDED
        assert payment.version == 3


class TestPaymentVersioning:
    """Тесты версионирования платежа."""

    def test_version_increments_on_confirm(self):
        payment = Payment(abonent_id=uuid4(), amount=100, currency="RUB", payment_method="cash")
        assert payment.version == 1

        payment.confirm()
        assert payment.version == 2

    def test_version_increments_on_refund(self):
        payment = Payment(abonent_id=uuid4(), amount=100, currency="RUB", payment_method="card")
        payment.confirm()
        assert payment.version == 2

        payment.refund()
        assert payment.version == 3

    def test_version_increments_on_fail(self):
        payment = Payment(abonent_id=uuid4(), amount=100, currency="RUB", payment_method="card")
        assert payment.version == 1

        payment.fail("timeout")
        assert payment.version == 2

    def test_version_preserved_on_creation(self):
        payment = Payment(
            abonent_id=uuid4(),
            amount=100,
            currency="RUB",
            payment_method="cash",
            version=7,
        )

        assert payment.version == 7
