"""Order and payment endpoint implementations."""

from __future__ import annotations

from typing import Any, Sequence, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...api.deps import (
    db_session,
    notification_dispatcher,
    razorpay_service,
    request_metadata,
    require_admin,
)
from ...core.config import get_settings
from ...repositories import cart as cart_repo
from ...repositories import orders as order_repo
from ...schemas.common import ErrorResponse, RequestMetadata
from ...schemas.orders import (
    OrderCancelResponse,
    OrderCreateRequest,
    OrderCreateResponse,
    OrderDetail,
    OrderDetailResponse,
    OrderSummary,
    OrdersListResponse,
    RazorpayWebhookResponse,
    RefundRequest,
    RefundResponse,
)
from ...services.razorpay import RazorpayWebhookVerificationError
from ...services.workflows import NotificationDispatcher

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_not_found(order_id: str) -> HTTPException:
    error = ErrorResponse(
        code="order_not_found",
        message="Order not found",
        details={"order_id": order_id},
    )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump()
    )


def _cart_missing(reference: str | None) -> HTTPException:
    error = ErrorResponse(
        code="cart_missing",
        message="A valid cart is required to create an order",
        details={"cart_reference": reference},
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


def _payment_missing(payment_id: str) -> HTTPException:
    error = ErrorResponse(
        code="payment_not_found",
        message="Payment not found",
        details={"payment_id": payment_id},
    )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump()
    )


def _cart_empty(cart_id: str) -> HTTPException:
    error = ErrorResponse(
        code="cart_empty",
        message="Cart contains no items",
        details={"cart_id": cart_id},
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


def _inventory_unavailable(cake_id: str) -> HTTPException:
    error = ErrorResponse(
        code="inventory_unavailable",
        message="Requested quantity exceeds available stock",
        details={"cake_id": cake_id},
    )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail=error.model_dump()
    )


def _cancellation_not_allowed(order_id: str) -> HTTPException:
    error = ErrorResponse(
        code="cancellation_not_allowed",
        message="Order can no longer be cancelled",
        details={"order_id": order_id},
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


def _razorpay_failure(reason: str) -> HTTPException:
    error = ErrorResponse(
        code="razorpay_unavailable",
        message="Failed to integrate with Razorpay",
        details={"reason": reason},
    )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY, detail=error.model_dump()
    )


def _invalid_webhook_signature() -> HTTPException:
    error = ErrorResponse(
        code="invalid_signature",
        message="Webhook signature verification failed",
        details=None,
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


def _invalid_webhook_payload(reason: str) -> HTTPException:
    error = ErrorResponse(
        code="invalid_webhook_payload",
        message="Unable to parse Razorpay webhook payload",
        details={"reason": reason},
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


def _cart_price_mismatch(
    cart_id: str,
    mismatches: Sequence[tuple[str, float, float]],
    tolerance: float,
) -> HTTPException:
    error = ErrorResponse(
        code="cart_price_mismatch",
        message="Cart pricing is outdated; refresh the cart before ordering",
        details={
            "cart_id": cart_id,
            "tolerance": tolerance,
            "items": [
                {
                    "cake_id": cake_id,
                    "catalog_price": expected,
                    "cart_price": actual,
                }
                for cake_id, expected, actual in mismatches
            ],
        },
    )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=error.model_dump(),
    )


@router.post("", response_model=OrderCreateResponse)
def create_order(
    payload: OrderCreateRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
    settings=Depends(get_settings),
    razorpay=Depends(razorpay_service),
) -> Any:
    cart_reference = payload.cart_id or payload.customer_id
    if not cart_reference:
        raise _cart_missing(None)

    try:
        cart = cart_repo.get_cart_by_reference(session, cart_reference)
    except cart_repo.CartNotFoundError as exc:
        raise _cart_missing(cart_reference) from exc

    try:
        order, created = order_repo.create_order(
            session,
            idempotency_key=payload.idempotency_key,
            cart=cart,
            customer_id=payload.customer_id,
            is_test=payload.is_test
            if payload.is_test is not None
            else settings.is_test_mode,
            pricing=cart_repo.PricingRules.from_settings(settings),
            price_match_tolerance=settings.price_match_tolerance,
            reservation_ttl_minutes=settings.order_reservation_ttl_minutes,
        )
    except order_repo.CartEmptyError as exc:
        raise _cart_empty(exc.args[0]) from exc
    except order_repo.InventoryUnavailableError as exc:
        missing_cake_id = exc.args[0] if exc.args else "unknown"
        raise _inventory_unavailable(missing_cake_id) from exc
    except cart_repo.CartPriceMismatchError as exc:
        tolerance = settings.price_match_tolerance
        raise _cart_price_mismatch(cart.cart_id, exc.mismatches, tolerance) from exc

    provider_order_id = order.provider_order_id
    if created and not order.provider_order_id:
        amount_paise = int(round(order.total * 100))
        try:
            razorpay_result = razorpay.create_order(
                amount_paise=amount_paise,
                currency=order.currency,
                receipt=order.order_id,
                notes={"cart_id": order.cart_id, "customer_id": order.customer_id},
                test_mode=order.is_test,
            )
        except Exception as exc:  # pragma: no cover - network interaction
            raise _razorpay_failure(str(exc)) from exc
        provider_order_id = razorpay_result.id
        order_repo.set_provider_order_reference(session, order, provider_order_id)

    detail = OrderDetail(**order_repo.serialize_order_detail(order))
    return OrderCreateResponse(
        order=detail,
        provider_order_id=provider_order_id or "",
        request=request,
    )


@router.get(
    "/{identifier}",
    response_model=Union[OrderDetailResponse, OrdersListResponse],
)
def get_order_or_orders(
    identifier: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Union[OrderDetailResponse, OrdersListResponse]:
    try:
        order = order_repo.get_order(session, identifier)
    except order_repo.OrderNotFoundError:
        orders = order_repo.list_orders(session, identifier)
        summaries = [
            OrderSummary(**order_repo.serialize_order_summary(order))
            for order in orders
        ]
        return OrdersListResponse(orders=summaries, request=request)

    detail = OrderDetail(**order_repo.serialize_order_detail(order))
    return OrderDetailResponse(order=detail, request=request)


@router.post("/{order_id}/cancel", response_model=OrderCancelResponse)
def cancel_order(
    order_id: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        order = order_repo.cancel_order(session, order_id)
    except order_repo.OrderNotFoundError as exc:
        raise _order_not_found(order_id) from exc
    except order_repo.OrderCancellationNotAllowedError as exc:
        raise _cancellation_not_allowed(order_id) from exc
    detail = OrderDetail(**order_repo.serialize_order_detail(order))
    return OrderCancelResponse(order=detail, request=request)


payments_router = APIRouter(prefix="/payments", tags=["payments"])


@payments_router.post("/webhook/razorpay", response_model=RazorpayWebhookResponse)
async def razorpay_webhook(
    http_request: Request,
    session: Session = Depends(db_session),
    metadata: RequestMetadata = Depends(request_metadata),
    razorpay=Depends(razorpay_service),
    dispatcher: NotificationDispatcher = Depends(notification_dispatcher),
) -> Any:
    raw_body = await http_request.body()
    headers = {key: value for key, value in http_request.headers.items()}
    signature = headers.get("X-Razorpay-Signature")

    try:
        razorpay.verify_webhook_signature(raw_body, signature)
    except RazorpayWebhookVerificationError as exc:
        raise _invalid_webhook_signature() from exc

    try:
        payload = await http_request.json()
    except Exception as exc:  # pragma: no cover - invalid JSON
        raise _invalid_webhook_payload(str(exc)) from exc

    order_repo.record_webhook(
        session,
        headers=headers,
        payload=payload,
        signature=signature or "",
    )

    order, payment = order_repo.apply_payment_event(session, payload)
    if order and payment and payment.status in {"captured", "authorized"}:
        dispatcher.send_order_confirmation(order)
        dispatcher.enqueue_post_payment_jobs(order)

    return RazorpayWebhookResponse(accepted=True, request=metadata)


@payments_router.post("/refund", response_model=RefundResponse)
def request_refund(
    payload: RefundRequest,
    _: None = Depends(require_admin),
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
    razorpay=Depends(razorpay_service),
) -> Any:
    try:
        payment = order_repo.get_payment(session, payload.payment_id)
    except order_repo.PaymentNotFoundError as exc:
        raise _payment_missing(payload.payment_id) from exc

    provider_payment_id = payment.provider_payment_id or payment.payment_id
    amount_paise = (
        int(round(payload.amount * 100)) if payload.amount is not None else None
    )

    try:
        refund_result = razorpay.request_refund(
            payment_id=provider_payment_id,
            amount_paise=amount_paise,
            notes={"reason": payload.reason} if payload.reason else None,
        )
    except Exception as exc:  # pragma: no cover - network interaction
        raise _razorpay_failure(str(exc)) from exc

    refund = order_repo.request_refund(
        session,
        payment=payment,
        amount=payload.amount,
        reason=payload.reason,
    )
    if refund_result.status:
        refund.status = refund_result.status
        if refund_result.status in {"processed", "completed", "success"}:
            payment.status = "refunded"
            payment.order.payment_status = "refunded"
            payment.order.status = "refunded"
    session.flush()
    return RefundResponse(
        payment_id=payment.payment_id,
        refund_id=refund.refund_id,
        status=refund.status,
        request=request,
    )


router.include_router(payments_router)
