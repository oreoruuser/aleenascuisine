"""Pydantic schemas for cake catalog operations."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, PositiveInt

from .common import RequestMetadata


class CakeFilters(BaseModel):
    search: Optional[str] = Field(None, description="Free text search term")
    category: Optional[str] = Field(None, description="Filter by cake category")
    min_price: Optional[float] = Field(
        None, description="Minimum price (inclusive) in major currency units"
    )
    max_price: Optional[float] = Field(
        None, description="Maximum price (inclusive) in major currency units"
    )
    page: PositiveInt = Field(1, description="Page number, starting at 1")
    page_size: PositiveInt = Field(20, description="Number of results per page")


class CakeSummary(BaseModel):
    cake_id: str
    name: str
    slug: str
    price: float
    currency: str
    category: Optional[str]
    is_available: bool


class CakeDetail(CakeSummary):
    description: Optional[str]
    image_url: Optional[str]
    stock_quantity: int
    created_at: datetime
    updated_at: datetime


class PaginatedCakesResponse(BaseModel):
    cakes: List[CakeSummary]
    total_count: int
    request: RequestMetadata


class CakeDetailResponse(BaseModel):
    cake: CakeDetail
    request: RequestMetadata
