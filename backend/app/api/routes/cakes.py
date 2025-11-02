"""Cake catalog contract endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import db_session, request_metadata
from ...repositories import cakes as cake_repo
from ...schemas.cakes import (
    CakeDetail,
    CakeDetailResponse,
    CakeSummary,
    PaginatedCakesResponse,
)
from ...schemas.common import ErrorResponse, RequestMetadata

router = APIRouter(prefix="/cakes", tags=["cakes"])


@router.get("", response_model=PaginatedCakesResponse)
def list_cakes(
    search: str | None = Query(None),
    category: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    cakes, total = cake_repo.list_cakes(
        session,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
    )
    summaries = [CakeSummary(**cake_repo.to_summary_dict(cake)) for cake in cakes]
    return PaginatedCakesResponse(cakes=summaries, total_count=total, request=request)


@router.get("/{cake_id}", response_model=CakeDetailResponse)
def get_cake(
    cake_id: str,
    request: RequestMetadata = Depends(request_metadata),
    session: Session = Depends(db_session),
) -> Any:
    try:
        cake = cake_repo.get_cake(session, cake_id)
    except cake_repo.CakeNotFoundError as exc:
        error = ErrorResponse(
            code="cake_not_found",
            message="Cake not found",
            details={"cake_id": cake_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=error.model_dump()
        ) from exc

    detail = CakeDetail(**cake_repo.to_detail_dict(cake))
    return CakeDetailResponse(cake=detail, request=request)
