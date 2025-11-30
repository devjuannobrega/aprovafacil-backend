from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mp_payment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    status: Mapped[str] = mapped_column(String(50))
    status_detail: Mapped[str | None] = mapped_column(String(100), nullable=True)

    transaction_amount: Mapped[float] = mapped_column(Float)
    installments: Mapped[int] = mapped_column(Integer, default=1)

    payment_method_id: Mapped[str] = mapped_column(String(50))
    payment_type_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    payer_email: Mapped[str] = mapped_column(String(255))
    payer_identification_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payer_identification_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
