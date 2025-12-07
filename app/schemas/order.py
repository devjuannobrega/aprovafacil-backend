from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    person_type: str = "pf"
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    person_type: str
    subtotal: Decimal
    total: Decimal
    notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
