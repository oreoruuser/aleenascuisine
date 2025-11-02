"""Cart management API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...api.deps import db_session, request_metadata
from ...repositories import cart as cart_repo
from ...schemas.cart import CartDeleteResponse, CartResponse, CartUpsertRequest
from ...schemas.common import ErrorResponse, RequestMetadata

router = APIRouter(prefix="/cart", tags=["cart"])


def _cart_not_found(reference: str) -> HTTPException:
    error = ErrorResponse(
        code="cart_not_found",
        message="Cart not found",
        details={"cart_reference": reference},
    )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump()
    )


def _cake_not_found() -> HTTPException:
    error = ErrorResponse(
        code="cart_item_cake_missing",
        message="One or more items reference unavailable cakes",
        details=None,
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


@router.post("", response_model=CartResponse, summary="Create or replace a cart")
def upsert_cart(
    payload: CartUpsertRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cart = cart_repo.upsert_cart(
            session,
            customer_id=payload.customer_id,
            cart_token=payload.cart_token,
            items=[item.model_dump() for item in payload.items],
        )
    except cart_repo.CartItemCakeNotFoundError as exc:
        raise _cake_not_found() from exc

    data = cart_repo.serialize_cart(cart)
    return CartResponse(**data, request=request)


@router.get("/{cart_reference}", response_model=CartResponse)
def get_cart(
    cart_reference: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cart = cart_repo.get_cart_by_reference(session, cart_reference)
    except cart_repo.CartNotFoundError as exc:
        raise _cart_not_found(cart_reference) from exc
    data = cart_repo.serialize_cart(cart)
    return CartResponse(**data, request=request)


@router.delete("/{cart_id}", response_model=CartDeleteResponse)
def delete_cart(
    cart_id: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    deleted = cart_repo.delete_cart(session, cart_id)
    return CartDeleteResponse(cart_id=cart_id, deleted=deleted, request=request)
