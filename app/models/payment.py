from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    PIX = "pix"
    BOLETO = "boleto"
    CREDIT_CARD = "credit_card"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    mp_payment_id = Column(String(100), nullable=True, index=True)
    mp_preference_id = Column(String(100), nullable=True)
    mp_external_reference = Column(String(100), nullable=True)
    method = Column(String(20), nullable=True)
    status = Column(String(20), default=PaymentStatus.PENDING.value)
    amount = Column(Numeric(10, 2), nullable=False)
    pix_qr_code = Column(Text, nullable=True)
    pix_qr_code_base64 = Column(Text, nullable=True)
    boleto_url = Column(String(500), nullable=True)
    boleto_barcode = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)

    order = relationship("Order", back_populates="payment")
