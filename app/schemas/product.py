from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class ProductCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price_pf: Decimal
    price_pj: Decimal


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_pf: Optional[Decimal] = None
    price_pj: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    price_pf: Decimal
    price_pj: Decimal
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
