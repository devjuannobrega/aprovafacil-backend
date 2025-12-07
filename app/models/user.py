from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, index=True, nullable=True)
    cnpj = Column(String(18), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    person_type = Column(String(2), default="pf")
    cep = Column(String(10), nullable=True)
    street = Column(String(255), nullable=True)
    number = Column(String(20), nullable=True)
    complement = Column(String(255), nullable=True)
    neighborhood = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(2), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    orders = relationship("Order", back_populates="user")
