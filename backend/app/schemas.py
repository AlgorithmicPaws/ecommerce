from sqlmodel import Field, SQLModel
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr, Field as PydanticField


# Pydantic Models for Request/Response Validation
class UserCreate(BaseModel):
    full_name: str = PydanticField(min_length=2, max_length=50)
    email: EmailStr
    password: str = PydanticField(min_length=8)
    phone: str = PydanticField(min_length=7, max_length=20)
    address: str = PydanticField(min_length=5, max_length=100)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str
    address: str
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class OrderCreate(BaseModel):
    user_id: int
    status: Optional[str] = "pending"


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class OrderItemCreate(BaseModel):
    order_id: int
    product_id: int
    quantity: int = 1  # Default to 1 if not specified


class OrderItemOut(BaseModel):
    order_id: int
    product_id: int
    quantity: int

    class Config:
        orm_mode = True


class ProductCreate(BaseModel):
    name: str
    merchant_id: int
    price: float = 0.0
    status: str = "active"


class ProductOut(BaseModel):
    id: int
    name: str
    merchant_id: int
    price: float
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class MerchantCreate(BaseModel):
    admin_id: Optional[int] = None
    merchant_name: str


class MerchantOut(BaseModel):
    id: int
    admin_id: Optional[int]
    merchant_name: str
    created_at: datetime

    class Config:
        orm_mode = True