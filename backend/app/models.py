from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Users(SQLModel, table=True):
    id: int = Field(primary_key=True)
    full_name: Optional[str]
    email: Optional[str] = Field(unique=True)
    password: str = Field()  # This will store the hashed password.
    gender: Optional[str]
    date_of_birth: Optional[str]
    created_at: Optional[str]

    orders: List["Orders"] = Relationship(back_populates="user")
    merchants: List["Merchants"] = Relationship(back_populates="admin")

class Orders(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    status: Optional[str]
    created_at: Optional[str]

    user: "Users" = Relationship(back_populates="orders")
    order_items: List["OrderItems"] = Relationship(back_populates="order")

class OrderItems(SQLModel, table=True):
    order_id: int = Field(foreign_key="orders.id", primary_key=True)
    product_id: int = Field(foreign_key="products.id", primary_key=True)
    quantity: Optional[int]

    order: "Orders" = Relationship(back_populates="order_items")
    product: "Products" = Relationship(back_populates="order_items")

class Products(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: Optional[str]
    merchant_id: int = Field(foreign_key="merchants.id", nullable=False)    
    price: Optional[int]
    status: Optional[str]
    created_at: Optional[str]

    order_items: List["OrderItems"] = Relationship(back_populates="product")
    merchant: "Merchants" = Relationship(back_populates="products")

class Merchants(SQLModel, table=True):
    id: int = Field(primary_key=True)
    admin_id: Optional[int] = Field(foreign_key="users.id")
    merchant_name: Optional[str]
    created_at: Optional[str]

    admin: "Users" = Relationship(back_populates="merchants")
    products: List["Products"] = Relationship(back_populates="merchant")
