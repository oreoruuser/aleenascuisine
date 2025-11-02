"""Reusable dependencies for FastAPI routers."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..db.session import get_db_session
from ..repositories import orders as order_repo
from ..schemas.common import ErrorResponse, RequestMetadata
from ..services.auth import (
    CognitoJWTVerifier,
    JWTVerificationError,
    Principal,
    principal_from_claims,
)
from ..services.invoices import InvoiceGenerationError, InvoiceService
from ..services.razorpay import RazorpayConfigurationError, RazorpayService
from ..services.workflows import (
    LoggingNotificationDispatcher,
    NotificationDispatcher,
    SQSNotificationDispatcher,
)
from .routes.utils import build_request_metadata


def request_metadata() -> RequestMetadata:
    """Generate request metadata for responses."""

    return RequestMetadata(**build_request_metadata())


_VERIFIER_CACHE: dict[tuple[str, bool, str | None], CognitoJWTVerifier] = {}


def _bearer_token(header_value: str | None) -> str:
    if not header_value or not header_value.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                code="unauthorized",
                message="Authorization header missing or invalid",
                details=None,
            ).model_dump(),
        )
    return header_value.split(" ", 1)[1]


def _get_verifier(settings) -> CognitoJWTVerifier:
    cache_key = (
        settings.cognito_user_pool_id or "test",
        settings.cognito_test_mode,
        settings.cognito_test_shared_secret,
    )
    verifier = _VERIFIER_CACHE.get(cache_key)
    if verifier is None:
        verifier = CognitoJWTVerifier(settings)
        _VERIFIER_CACHE[cache_key] = verifier
    return verifier


def get_current_principal(
    authorization: str | None = Header(default=None, alias="Authorization"),
    settings=Depends(get_settings),
) -> Principal:
    token = _bearer_token(authorization)
    verifier = _get_verifier(settings)
    try:
        claims = verifier.verify(token)
    except JWTVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                code="unauthorized",
                message="Invalid bearer token",
                details={"reason": str(exc)},
            ).model_dump(),
        ) from exc
    return principal_from_claims(claims)


def require_admin(
    principal: Principal = Depends(get_current_principal),
    settings=Depends(get_settings),
) -> Principal:
    admin_group = settings.cognito_admin_group
    principal_groups = {group.lower() for group in principal.groups}
    if admin_group and admin_group.lower() not in principal_groups:
        error = ErrorResponse(
            code="admin_access_required",
            message="Administrator privileges required",
            details={"required_group": admin_group},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.model_dump(),
        )
    return principal


def db_session(settings=Depends(get_settings)) -> Iterator[Session]:
    """Provide a transactional database session."""

    database_url = settings.database_url or "sqlite:///./aleena_dev.db"
    session_iter = get_db_session(database_url)
    session = next(session_iter)
    try:
        if settings.order_reservation_ttl_minutes > 0:
            order_repo.expire_stale_reservations(session)
        yield session
    finally:
        try:
            next(session_iter)
        except StopIteration:
            pass


@lru_cache(maxsize=1)
def _cached_razorpay_service(
    key_id: str, key_secret: str, webhook_secret: str | None
) -> RazorpayService:
    return RazorpayService(
        key_id=key_id,
        key_secret=key_secret,
        webhook_secret=webhook_secret,
    )


def razorpay_service(settings=Depends(get_settings)) -> RazorpayService:
    """Return a Razorpay service instance configured from environment settings."""

    key_id = settings.razorpay_key_id
    key_secret = settings.razorpay_key_secret
    if not key_id or not key_secret:
        error = ErrorResponse(
            code="razorpay_not_configured",
            message="Razorpay credentials are not configured",
            details=None,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        )
    try:
        return _cached_razorpay_service(
            key_id, key_secret, settings.razorpay_webhook_secret
        )
    except RazorpayConfigurationError as exc:  # pragma: no cover - defensive
        error = ErrorResponse(
            code="razorpay_setup_failed",
            message="Unable to initialize Razorpay client",
            details={"error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.model_dump(),
        ) from exc


def notification_dispatcher() -> NotificationDispatcher:
    """Provide a notification dispatcher for post-payment workflows."""

    settings = get_settings()
    if settings.post_payment_queue_url:
        try:
            return SQSNotificationDispatcher(settings.post_payment_queue_url)
        except Exception:  # pragma: no cover - boto client errors
            return LoggingNotificationDispatcher()
    return LoggingNotificationDispatcher()


def invoice_service(settings=Depends(get_settings)) -> InvoiceService:
    """Provide an invoice generator for background tasks."""

    try:
        return InvoiceService(settings)
    except InvoiceGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="invoice_generation_unavailable",
                message="Invoice generation service is not configured",
                details={"reason": str(exc)},
            ).model_dump(),
        ) from exc
