"""Authentication related API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.config import get_settings
from ...schemas.auth import ConfirmSignupRequest, ConfirmSignupResponse
from ...schemas.common import ErrorResponse
from ...services.auth import CognitoSignupConfirmationError, confirm_user_signup

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/confirm",
    response_model=ConfirmSignupResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm a hosted UI sign up",
)
def confirm_signup(
    payload: ConfirmSignupRequest, settings=Depends(get_settings)
) -> ConfirmSignupResponse:
    """Confirm a Cognito sign up using the verification code sent via email."""

    try:
        confirm_user_signup(settings, payload.username, payload.code)
    except CognitoSignupConfirmationError as exc:
        detail = ErrorResponse(
            code="signup_confirmation_failed",
            message=str(exc),
            details=None,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail.model_dump(),
        ) from exc

    return ConfirmSignupResponse()
