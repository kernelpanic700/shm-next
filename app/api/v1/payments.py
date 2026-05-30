# =============================================================================
# shm-next — API v1: Payments
# =============================================================================
"""Эндпоинты для управления платежами."""

from datetime import datetime
from uuid import UUID

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.status_codes import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.api.dependencies import get_payment_service, provide_uow_dependency
from app.api.dto.requests import PaymentCreate
from app.api.dto.responses import PaymentListResponse, PaymentResponse
from app.core.application.payments.payment_service import PaymentService
from app.infrastructure.db.unit_of_work import UnitOfWork


def _request_permissions(request: Request) -> list[str]:
    return request.scope.get("state", {}).get("permissions", [])


def _is_admin_request(request: Request) -> bool:
    return "*" in _request_permissions(request)


def _request_user_uuid(request: Request) -> UUID | None:
    user_id = request.scope.get("state", {}).get("user_id")
    if not user_id or str(user_id).startswith("admin:"):
        return None
    try:
        return UUID(str(user_id))
    except ValueError:
        return None


def _payment_abonent_id(payment: dict) -> UUID | None:
    abonent_id = payment.get("abonent_id")
    if abonent_id is None:
        return None
    return UUID(str(abonent_id))


def _ensure_payment_scope(request: Request, abonent_id: UUID | None) -> None:
    if _is_admin_request(request):
        return
    user_id = _request_user_uuid(request)
    if user_id is None or abonent_id != user_id:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")


class PaymentController(Controller):
    """Контроллер для управления платежами."""

    path = "/payments"
    tags = ["Payments"]

    dependencies = {
        "uow": Provide(provide_uow_dependency),
        "payment_service": Provide(get_payment_service, sync_to_thread=False),
    }

    @get("/", summary="Список платежей")
    async def list_payments(
        self,
        request: Request,
        payment_service: PaymentService,
        abonent_id: UUID | None = Parameter(query="abonent_id", required=False),
        from_date: datetime | None = Parameter(query="from_date", required=False),
        to_date: datetime | None = Parameter(query="to_date", required=False),
        status: str | None = Parameter(query="status", required=False),
        page: int = 1,
        per_page: int = 50,
    ) -> PaymentListResponse:
        """Получить список платежей (опционально фильтр по абоненту)."""
        if not _is_admin_request(request):
            _ensure_payment_scope(request, abonent_id)

        if abonent_id:
            payments = await payment_service.get_payments_by_abonent(
                abonent_id=abonent_id,
                from_date=from_date,
                to_date=to_date,
                limit=per_page,
            )
        else:
            # Получаем все платежи без фильтрации по абоненту
            payments = await payment_service.get_all_payments(
                from_date=from_date,
                to_date=to_date,
                limit=per_page,
            )
        return PaymentListResponse(
            items=payments,
            total=len(payments),
            page=page,
            per_page=per_page,
        )

    @get("/{payment_id:uuid}", summary="Получить платёж")
    async def get_payment(
        self,
        request: Request,
        payment_id: UUID,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Получить платёж по ID."""
        payment = await payment_service.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Payment not found")
        _ensure_payment_scope(request, _payment_abonent_id(payment))
        return PaymentResponse.model_validate(payment, from_attributes=True)

    @post("/", summary="Создать платёж", status_code=HTTP_201_CREATED)
    async def create_payment(
        self,
        request: Request,
        data: PaymentCreate,
        uow: UnitOfWork,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Создать новый платёж."""
        _ensure_payment_scope(request, data.abonent_id)
        async with uow:
            try:
                payment = await payment_service.create_payment(
                    abonent_id=data.abonent_id,
                    amount=data.amount,
                    currency=data.currency,
                    payment_method=data.payment_method,
                    external_id=data.external_id,
                )
            except ValueError as exc:
                status_code = (
                    HTTP_404_NOT_FOUND if "not found" in str(exc) else HTTP_400_BAD_REQUEST
                )
                raise HTTPException(status_code=status_code, detail=str(exc)) from exc
            await uow.commit()
            return PaymentResponse.model_validate(payment, from_attributes=True)

    @post("/{payment_id:uuid}/confirm", summary="Подтвердить платёж")
    async def confirm_payment(
        self,
        payment_id: UUID,
        uow: UnitOfWork,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Подтвердить платёж."""
        async with uow:
            try:
                result = await payment_service.confirm_payment(payment_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=str(exc),
                ) from exc
            if not result:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Payment not found")
            payment = await payment_service.get_payment(payment_id)
            await uow.commit()
            return PaymentResponse.model_validate(payment, from_attributes=True)

    @post("/{payment_id:uuid}/refund", summary="Возврат платежа")
    async def refund_payment(
        self,
        payment_id: UUID,
        uow: UnitOfWork,
        payment_service: PaymentService,
    ) -> PaymentResponse:
        """Выполнить возврат платежа."""
        async with uow:
            try:
                result = await payment_service.refund_payment(payment_id)
            except ValueError as exc:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            if not result:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Payment not found")
            payment = await payment_service.get_payment(payment_id)
            await uow.commit()
            return PaymentResponse.model_validate(payment, from_attributes=True)
