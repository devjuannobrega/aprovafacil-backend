from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    person_type: str = "pf"
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    cep: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    person_type: Optional[str] = None
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    cep: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    person_type: str = "pf"
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    cep: Optional[str] = None
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
