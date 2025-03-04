from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Annotated
from datetime import datetime
from pydantic import BaseModel, EmailStr


# Pydantic Models for Request/Response Validation
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    gender: Optional[str]
    date_of_birth: Optional[str]

class UserOut(BaseModel):
    id: int
    full_name: Optional[str]
    email: EmailStr
    gender: Optional[str]
    date_of_birth: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    
class OrderCreate(SQLModel):
    user_id: int
    status: Optional[str] = None

class OrderItemCreate(SQLModel):
    order_id: int
    product_id: int
    quantity: Optional[int] = None

class ProductCreate(SQLModel):
    name: Optional[str] = None
    merchant_id: int
    price: Optional[int] = None
    status: Optional[str] = None
    category_id: Optional[int] = None

class MerchantCreate(SQLModel):
    admin_id: Optional[int] = None
    merchant_name: Optional[str] = None