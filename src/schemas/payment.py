from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class PayerIdentification(BaseModel):
    type: str
    number: str


class Payer(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    identification: Optional[PayerIdentification] = None


class PaymentRequest(BaseModel):
    token: str
    transaction_amount: float
    installments: int
    payment_method_id: str
    issuer_id: Optional[str] = None
    payer: Payer
    description: Optional[str] = None
    external_reference: Optional[str] = None


class PaymentResponse(BaseModel):
    id: int
    mp_payment_id: str
    status: str
    status_detail: Optional[str] = None
    transaction_amount: float
    installments: int
    payment_method_id: str
    payer_email: str
    created_at: datetime

    class Config:
        from_attributes = True


class PreferenceItem(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    quantity: int
    unit_price: float
    currency_id: str = "BRL"


class PreferenceRequest(BaseModel):
    items: List[PreferenceItem]
    payer: Optional[Payer] = None
    external_reference: Optional[str] = None
    notification_url: Optional[str] = None


class PreferenceResponse(BaseModel):
    preference_id: str
    init_point: str
    sandbox_init_point: str


class WebhookPayload(BaseModel):
    action: Optional[str] = None
    api_version: Optional[str] = None
    data: Optional[dict] = None
    date_created: Optional[str] = None
    id: Optional[int] = None
    live_mode: Optional[bool] = None
    type: Optional[str] = None
    user_id: Optional[str] = None
