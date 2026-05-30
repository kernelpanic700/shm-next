# =============================================================================
# shm-next — PaymentService Tests
# =============================================================================
"""Тесты для PaymentService (application layer)."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.application.payments.payment_service import PaymentService
from app.core.domain.entities.abonent import Abonent
from app.core.domain.entities.invoice import Invoice, InvoiceStatus
from app.core.domain.value_objects import Money


class TestPaymentService:
    """Тесты PaymentService."""

    def setup_method(self):
        self.payment_repo = AsyncMock()
        self.abonent_repo = AsyncMock()
        self.invoice_repo = AsyncMock()
        self.event_bus = AsyncMock()
        self.service = PaymentService(
            payment_repo=self.payment_repo,
            abonent_repo=self.abonent_repo,
            event_bus=self.event_bus,
            invoice_repo=self.invoice_repo,
        )

    @pytest.mark.asyncio
    async def test_create_payment_success(self):
        """Создание платежа — успех."""
        abonent_id = uuid4()
        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(1000.0, "RUB"),
        )
        self.abonent_repo.get.return_value = abonent
        self.payment_repo.create.return_value = uuid4()

        result = await self.service.create_payment(
            abonent_id=abonent_id,
            amount=500.0,
            currency="RUB",
            payment_method="card",
        )

        assert result is not None
        assert result.amount == 500.0
        assert result.currency == "RUB"
        assert result.payment_method == "card"
        self.payment_repo.create.assert_called_once()
        self.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_payment_abonent_not_found(self):
        """Создание платежа — абонент не найден."""
        self.abonent_repo.get.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await self.service.create_payment(
                abonent_id=uuid4(),
                amount=500.0,
                currency="RUB",
                payment_method="cash",
            )

        self.payment_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_payment_invalid_amount(self):
        """Создание платежа — некорректная сумма."""
        abonent_id = uuid4()
        abonent = Abonent(
            id=abonent_id,
            full_name="Тест",
            balance=Money(1000.0, "RUB"),
        )
        self.abonent_repo.get.return_value = abonent

        with pytest.raises(ValueError, match="positive"):
            await self.service.create_payment(
                abonent_id=abonent_id,
                amount=-100.0,
                currency="RUB",
                payment_method="cash",
            )

        with pytest.raises(ValueError, match="positive"):
            await self.service.create_payment(
                abonent_id=abonent_id,
                amount=0.0,
                currency="RUB",
                payment_method="cash",
            )

    @pytest.mark.asyncio
    async def test_get_payment(self):
        """Получение платежа по ID."""
        payment_id = uuid4()
        expected = {
            "id": str(payment_id),
            "abonent_id": str(uuid4()),
            "amount": 500.0,
            "currency": "RUB",
            "status": "COMPLETED",
        }
        self.payment_repo.get.return_value = expected

        result = await self.service.get_payment(payment_id)

        assert result == expected

    @pytest.mark.asyncio
    async def test_get_payment_not_found(self):
        """Получение платежа — не найден."""
        self.payment_repo.get.return_value = None

        result = await self.service.get_payment(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_payments_by_abonent(self):
        """Получение истории платежей абонента."""
        payments = [
            {"id": str(uuid4()), "amount": 100.0, "currency": "RUB"},
            {"id": str(uuid4()), "amount": 200.0, "currency": "RUB"},
        ]
        self.payment_repo.get_by_abonent.return_value = payments

        result = await self.service.get_payments_by_abonent(uuid4())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_confirm_payment_success(self):
        """Подтверждение платежа — успех."""
        payment_id = uuid4()
        abonent_id = uuid4()
        abonent = Abonent(id=abonent_id, balance=Money(1000, "RUB"))
        self.payment_repo.get.return_value = {
            "id": str(payment_id),
            "abonent_id": str(abonent_id),
            "amount": 500.0,
            "currency": "RUB",
            "status": "NEW",
        }
        self.payment_repo.confirm.return_value = True
        self.abonent_repo.get.return_value = abonent
        self.abonent_repo.save.return_value = abonent

        result = await self.service.confirm_payment(payment_id)

        assert result is True
        assert abonent.balance.amount == 1500
        self.abonent_repo.save.assert_called_once_with(abonent)

    @pytest.mark.asyncio
    async def test_confirm_payment_failed(self):
        """Подтверждение платежа — не найден."""
        self.payment_repo.get.return_value = {
            "id": str(uuid4()),
            "abonent_id": str(uuid4()),
            "amount": 500.0,
            "currency": "RUB",
            "status": "COMPLETED",
        }
        self.payment_repo.confirm.return_value = False

        result = await self.service.confirm_payment(uuid4())

        assert result is False
        self.abonent_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_refund_payment_success(self):
        """Возврат платежа — успех."""
        payment_id = uuid4()
        abonent_id = uuid4()
        abonent = Abonent(id=abonent_id, balance=Money(1000, "RUB"))
        self.payment_repo.get.return_value = {
            "id": str(payment_id),
            "abonent_id": str(abonent_id),
            "amount": 300.0,
            "currency": "RUB",
            "status": "COMPLETED",
        }
        self.payment_repo.refund.return_value = True
        self.abonent_repo.get.return_value = abonent
        self.abonent_repo.save.return_value = abonent
        self.invoice_repo.get.return_value = None

        result = await self.service.refund_payment(payment_id)

        assert result is True
        assert abonent.balance.amount == 700
        self.abonent_repo.save.assert_called_once_with(abonent)

    @pytest.mark.asyncio
    async def test_refund_payment_marks_linked_invoice_unpaid(self):
        """Возврат оплаты счёта возвращает счёт в ISSUED."""
        payment_id = uuid4()
        abonent_id = uuid4()
        invoice_id = uuid4()
        abonent = Abonent(id=abonent_id, balance=Money(1000, "RUB"))
        invoice = Invoice(
            id=invoice_id,
            abonent_id=abonent_id,
            amount=300,
            status=InvoiceStatus.PAID,
        )
        self.payment_repo.get.return_value = {
            "id": str(payment_id),
            "abonent_id": str(abonent_id),
            "amount": 300.0,
            "currency": "RUB",
            "status": "COMPLETED",
            "external_id": f"invoice:{invoice_id}:provider-123",
        }
        self.payment_repo.refund.return_value = True
        self.abonent_repo.get.return_value = abonent
        self.abonent_repo.save.return_value = abonent
        self.invoice_repo.get.return_value = invoice
        self.invoice_repo.save.return_value = invoice

        result = await self.service.refund_payment(payment_id)

        assert result is True
        assert invoice.status == InvoiceStatus.ISSUED
        self.invoice_repo.get.assert_called_once_with(invoice_id)
        self.invoice_repo.save.assert_called_once_with(invoice)

    @pytest.mark.asyncio
    async def test_refund_payment_failed(self):
        """Возврат платежа — не найден."""
        self.payment_repo.get.return_value = {
            "id": str(uuid4()),
            "abonent_id": str(uuid4()),
            "amount": 300.0,
            "currency": "RUB",
            "status": "NEW",
        }
        self.payment_repo.refund.return_value = False

        result = await self.service.refund_payment(uuid4())

        assert result is False
        self.abonent_repo.save.assert_not_called()
