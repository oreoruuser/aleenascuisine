"""Administrative API endpoints for managing catalog content."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...api.deps import db_session, request_metadata, require_admin
from ...db.models import Cake
from ...repositories import cakes as cake_repo
from ...repositories import orders as order_repo
from ...schemas.admin import (
    AdminActionResponse,
    CakeAvailabilityRequest,
    CakeCreateRequest,
    CakeUpdateRequest,
    InventoryAdjustmentRequest,
    OrderStatusUpdateRequest,
)
from ...schemas.cakes import CakeDetail, CakeDetailResponse
from ...schemas.orders import OrderDetail, OrderDetailResponse
from ...schemas.common import ErrorResponse, RequestMetadata

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


def _serialize_cake_response(
    cake: Cake, request: RequestMetadata
) -> CakeDetailResponse:
    detail = CakeDetail(**cake.to_dict())
    return CakeDetailResponse(cake=detail, request=request)


def _not_found(cake_id: str) -> HTTPException:
    error = ErrorResponse(
        code="cake_not_found",
        message="Cake not found",
        details={"cake_id": cake_id},
    )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump()
    )


def _inventory_error(cake_id: str) -> HTTPException:
    error = ErrorResponse(
        code="inventory_adjustment_invalid",
        message="Inventory adjustment would result in negative stock",
        details={"cake_id": cake_id},
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


def _duplicate_slug(slug: str) -> HTTPException:
    error = ErrorResponse(
        code="cake_slug_conflict",
        message="A cake with this slug already exists",
        details={"slug": slug},
    )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail=error.model_dump()
    )


def _order_not_found(order_id: str) -> HTTPException:
    error = ErrorResponse(
        code="order_not_found",
        message="Order not found",
        details={"order_id": order_id},
    )
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump()
    )


def _invalid_status_transition(order_id: str, status: str) -> HTTPException:
    error = ErrorResponse(
        code="invalid_status_transition",
        message="Order status update is not permitted",
        details={"order_id": order_id, "target_status": status},
    )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail=error.model_dump()
    )


@router.post("/cakes", response_model=CakeDetailResponse, summary="Create a new cake")
def create_cake(
    payload: CakeCreateRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake = cake_repo.create_cake(
            session,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            category=payload.category,
            is_available=payload.is_available,
            stock_quantity=payload.stock_quantity,
            image_url=payload.image_url,
        )
    except cake_repo.DuplicateCakeSlugError as exc:
        raise _duplicate_slug(payload.slug) from exc
    return _serialize_cake_response(cake, request)


@router.patch("/cakes/{cake_id}", response_model=CakeDetailResponse)
def update_cake(
    cake_id: str,
    payload: CakeUpdateRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake = cake_repo.update_cake(
            session,
            cake_id,
            name=payload.name,
            description=payload.description,
            price=payload.price,
            currency=payload.currency,
            category=payload.category,
            is_available=payload.is_available,
            stock_quantity=payload.stock_quantity,
            image_url=payload.image_url,
        )
    except cake_repo.CakeNotFoundError as exc:
        raise _not_found(cake_id) from exc
    except cake_repo.InvalidInventoryAdjustmentError as exc:
        raise _inventory_error(cake_id) from exc
    return _serialize_cake_response(cake, request)


@router.patch("/cakes/{cake_id}/availability", response_model=CakeDetailResponse)
def update_cake_availability(
    cake_id: str,
    payload: CakeAvailabilityRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake = cake_repo.set_availability(session, cake_id, payload.is_available)
    except cake_repo.CakeNotFoundError as exc:
        raise _not_found(cake_id) from exc
    return _serialize_cake_response(cake, request)


@router.post("/cakes/{cake_id}/inventory", response_model=CakeDetailResponse)
def adjust_inventory(
    cake_id: str,
    payload: InventoryAdjustmentRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake = cake_repo.adjust_inventory(session, cake_id, payload.delta)
    except cake_repo.CakeNotFoundError as exc:
        raise _not_found(cake_id) from exc
    except cake_repo.InvalidInventoryAdjustmentError as exc:
        raise _inventory_error(cake_id) from exc
    return _serialize_cake_response(cake, request)


@router.post("/cakes/{cake_id}/publish", response_model=AdminActionResponse)
def publish_cake(
    cake_id: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake_repo.set_availability(session, cake_id, True)
    except cake_repo.CakeNotFoundError as exc:
        raise _not_found(cake_id) from exc
    return AdminActionResponse(success=True, request=request)


@router.post("/cakes/{cake_id}/unpublish", response_model=AdminActionResponse)
def unpublish_cake(
    cake_id: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake_repo.set_availability(session, cake_id, False)
    except cake_repo.CakeNotFoundError as exc:
        raise _not_found(cake_id) from exc
    return AdminActionResponse(success=True, request=request)


@router.post("/orders/{order_id}/status", response_model=OrderDetailResponse)
def update_order_status(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        order = order_repo.update_order_status(session, order_id, payload.status)
    except order_repo.OrderNotFoundError as exc:
        raise _order_not_found(order_id) from exc
    except order_repo.OrderStatusUpdateError as exc:
        raise _invalid_status_transition(order_id, payload.status) from exc
    detail = OrderDetail(**order_repo.serialize_order_detail(order))
    return OrderDetailResponse(order=detail, request=request)
