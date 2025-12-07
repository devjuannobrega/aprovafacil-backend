from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime


class PaymentPreferenceCreate(BaseModel):
    order_id: int
    payment_method: str


class CardPaymentCreate(BaseModel):
    order_id: int
    token: str
    installments: int = 1
    payment_method_id: str
    issuer_id: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    mp_payment_id: Optional[str] = None
    method: Optional[str] = None
    status: str
    amount: Decimal
    pix_qr_code: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentPreferenceResponse(BaseModel):
    preference_id: str
    init_point: str
    sandbox_init_point: Optional[str] = None
