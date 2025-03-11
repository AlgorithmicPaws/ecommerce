from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str  # Changed from Optional to required
    email: str = Field(unique=True)  # Changed from Optional to required
    password: str
    phone: str
    address: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)  # Changed to datetime type

    orders: List["Orders"] = Relationship(back_populates="user")
    merchants: List["Merchants"] = Relationship(back_populates="admin")
    
class Orders(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    status: Optional[str] = Field(default="pending")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)  # Changed to datetime type

    user: "Users" = Relationship(back_populates="orders")
    order_items: List["OrderItems"] = Relationship(back_populates="order")

class OrderItems(SQLModel, table=True):
    order_id: int = Field(foreign_key="orders.id", primary_key=True)
    product_id: int = Field(foreign_key="products.id", primary_key=True)
    quantity: int = Field(default=1)  # Changed from Optional to required with default

    order: "Orders" = Relationship(back_populates="order_items")
    product: "Products" = Relationship(back_populates="order_items")

class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # Changed from Optional to required
    merchant_id: int = Field(foreign_key="merchants.id", nullable=False)    
    price: float = Field(default=0.0)  # Changed from Optional int to required float with default
    status: str = Field(default="active")  # Changed from Optional to required with default
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)  # Changed to datetime type

    order_items: List["OrderItems"] = Relationship(back_populates="product")
    merchant: "Merchants" = Relationship(back_populates="products")

class Merchants(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: Optional[int] = Field(foreign_key="users.id", nullable=True)
    merchant_name: str  # Changed from Optional to required
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)  # Changed to datetime type

    admin: Optional["Users"] = Relationship(back_populates="merchants")
    products: List["Products"] = Relationship(back_populates="merchant")