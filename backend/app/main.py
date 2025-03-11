from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select
from datetime import datetime, timedelta

# Import models and schemas
from app.models import Session, Users, Orders, Products, Merchants, OrderItems
from app.schemas import (
    UserCreate, UserOut, Token, TokenData, 
    OrderCreate, OrderOut, 
    OrderItemCreate, OrderItemOut,
    ProductCreate, ProductOut,
    MerchantCreate, MerchantOut
)
from app.db import engine, init_db, get_session
from app.middleware import setup_middleware

# Initialize FastAPI app
app = FastAPI(title="E-commerce API")

# Apply middleware (CORS, etc.)
setup_middleware(app)

# Initialize database
init_db()

# User update schema
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    address: Optional[str] = Field(None, min_length=5, max_length=100)
    
    class Config:
        orm_mode = True

#==============================================
# AUTHENTICATION CONFIGURATION
#==============================================

# Security settings
SECRET_KEY = "your-secure-secret-key"  # In production, use a secure secret key and env variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Password utility functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# User authentication dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    statement = select(Users).where(Users.email == token_data.email)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

# Utility function to check merchant admin permissions
def is_merchant_admin(merchant_id: int, user_id: int, session: Session):
    merchant = session.get(Merchants, merchant_id)
    if not merchant or merchant.admin_id != user_id:
        return False
    return True

#==============================================
# AUTHENTICATION ENDPOINTS
#==============================================

@app.post("/api/auth/login", response_model=Token, tags=["Authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    session: Session = Depends(get_session)
):
    # Find the user by email (username field contains email in OAuth2 form)
    statement = select(Users).where(Users.email == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with expiration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

#==============================================
# USER ENDPOINTS
#==============================================

@app.post("/api/users/register", response_model=UserOut, tags=["Users"])
async def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
    # Check if email already exists
    statement = select(Users).where(Users.email == user_data.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create new user
    new_user = Users(
        full_name=user_data.full_name,
        email=user_data.email,
        password=hashed_password,
        phone=user_data.phone,
        address=user_data.address
        # created_at will be set by default_factory
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user

@app.get("/api/users/me", response_model=UserOut, tags=["Users"])
async def get_user_profile(current_user: Users = Depends(get_current_user)):
    """Get the current authenticated user's profile"""
    return current_user

@app.put("/api/users/me", response_model=UserOut, tags=["Users"])
async def update_user_profile(
    user_update: UserUpdate,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update the current authenticated user's profile"""
    
    # If email is being updated, check that it's not already in use
    if user_update.email and user_update.email != current_user.email:
        statement = select(Users).where(Users.email == user_update.email)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user attributes if provided
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    # Save changes
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user

@app.put("/api/users/change-password", response_model=dict, tags=["Users"])
async def change_password(
    current_password: str,
    new_password: str = Field(..., min_length=8),
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Allow users to change their password"""
    
    # Verify current password
    if not verify_password(current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Set new password
    current_user.password = get_password_hash(new_password)
    
    session.add(current_user)
    session.commit()
    
    return {"message": "Password updated successfully"}

#==============================================
# ORDER ENDPOINTS
#==============================================

@app.post("/api/orders", response_model=OrderOut, tags=["Orders"])
async def create_order(
    order: OrderCreate, 
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Users can only create orders for themselves
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create orders for other users"
        )
        
    new_order = Orders(
        user_id=current_user.id,  # Always use the authenticated user's ID
        status=order.status or "pending"
        # created_at will be set automatically by default_factory
    )
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    return new_order

@app.get("/api/orders", response_model=List[OrderOut], tags=["Orders"])
async def list_orders(
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Users can only see their own orders
    orders = session.exec(
        select(Orders).where(Orders.user_id == current_user.id)
    ).all()
    return orders

@app.get("/api/orders/{order_id}", response_model=OrderOut, tags=["Orders"])
async def get_order(
    order_id: int, 
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    order = session.get(Orders, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order"
        )
    
    return order

#==============================================
# ORDER ITEM ENDPOINTS
#==============================================

@app.post("/api/order-items", response_model=OrderItemOut, tags=["OrderItems"])
async def create_order_item(
    item: OrderItemCreate, 
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Verify the order exists
    order = session.get(Orders, item.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this order"
        )
    
    # Verify the product exists
    product = session.get(Products, item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if product is active
    if product.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not available for purchase"
        )
    
    # Check if item already exists in order
    existing_item = session.get(OrderItems, (item.order_id, item.product_id))
    if existing_item:
        # Update quantity instead of creating new
        existing_item.quantity += item.quantity
        session.add(existing_item)
        session.commit()
        session.refresh(existing_item)
        return existing_item
    
    # Create new order item
    new_item = OrderItems(
        order_id=item.order_id,
        product_id=item.product_id,
        quantity=item.quantity
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return new_item

@app.get("/api/order-items", response_model=List[OrderItemOut], tags=["OrderItems"])
async def list_order_items(
    order_id: Optional[int] = None,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Base query
    query = select(OrderItems)
    
    # Filter by order_id if provided
    if order_id:
        # Check if the order belongs to the current user
        order = session.get(Orders, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this order"
            )
        
        query = query.where(OrderItems.order_id == order_id)
    else:
        # Only return order items for orders owned by current user
        user_orders = session.exec(
            select(Orders.id).where(Orders.user_id == current_user.id)
        ).all()
        if not user_orders:
            return []
        
        query = query.where(OrderItems.order_id.in_(user_orders))
    
    items = session.exec(query).all()
    return items

#==============================================
# PRODUCT ENDPOINTS
#==============================================

@app.post("/api/products", response_model=ProductOut, tags=["Products"])
async def create_product(
    product: ProductCreate,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Verify that the merchant exists
    merchant = session.get(Merchants, product.merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Verify that the current user is the merchant admin
    if not is_merchant_admin(product.merchant_id, current_user.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You don't have permission to create products for this merchant"
        )
    
    # Create the product
    new_product = Products(
        name=product.name,
        merchant_id=product.merchant_id,
        price=product.price,
        status=product.status
        # created_at will be set by default_factory
    )
    
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    return new_product

@app.get("/api/products", response_model=List[ProductOut], tags=["Products"])
async def list_products(
    merchant_id: Optional[int] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Products)
    
    # Apply filters if provided
    if merchant_id:
        query = query.where(Products.merchant_id == merchant_id)
    if status:
        query = query.where(Products.status == status)
    
    products = session.exec(query).all()
    return products

@app.get("/api/products/{product_id}", response_model=ProductOut, tags=["Products"])
async def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/api/products/{product_id}", response_model=ProductOut, tags=["Products"])
async def update_product(
    product_id: int,
    product_update: ProductCreate,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Check if product exists
    existing_product = session.get(Products, product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has permission to update this product
    if not is_merchant_admin(existing_product.merchant_id, current_user.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this product"
        )
    
    # If trying to change merchant, verify user has permission for new merchant too
    if product_update.merchant_id != existing_product.merchant_id:
        if not is_merchant_admin(product_update.merchant_id, current_user.id, session):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to move this product to the specified merchant"
            )
    
    # Update product fields
    product_data = product_update.model_dump(exclude_unset=True)
    for key, value in product_data.items():
        setattr(existing_product, key, value)
    
    session.add(existing_product)
    session.commit()
    session.refresh(existing_product)
    return existing_product

@app.delete("/api/products/{product_id}", response_model=dict, tags=["Products"])
async def delete_product(
    product_id: int,
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Check if product exists
    product = session.get(Products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has permission to delete this product
    if not is_merchant_admin(product.merchant_id, current_user.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this product"
        )
    
    # Check if product is in any order (to maintain data integrity)
    order_item = session.exec(
        select(OrderItems).where(OrderItems.product_id == product_id)
    ).first()
    
    if order_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete product that is referenced in orders"
        )
    
    session.delete(product)
    session.commit()
    return {"ok": True, "message": "Product deleted successfully"}

#==============================================
# MERCHANT ENDPOINTS
#==============================================

@app.post("/api/merchants", response_model=MerchantOut, tags=["Merchants"])
async def create_merchant(
    merchant: MerchantCreate, 
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Set current user as admin if not specified
    admin_id = merchant.admin_id if merchant.admin_id else current_user.id
    
    # Only allow creating merchants for yourself (unless implementing admin features)
    if admin_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create merchants for other users"
        )
    
    new_merchant = Merchants(
        admin_id=admin_id,
        merchant_name=merchant.merchant_name
        # created_at will be set automatically by default_factory
    )
    session.add(new_merchant)
    session.commit()
    session.refresh(new_merchant)
    return new_merchant

@app.get("/api/merchants", response_model=List[MerchantOut], tags=["Merchants"])
async def list_merchants(
    admin_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    query = select(Merchants)
    
    if admin_id:
        query = query.where(Merchants.admin_id == admin_id)
    
    merchants = session.exec(query).all()
    return merchants

@app.get("/api/merchants/{merchant_id}", response_model=MerchantOut, tags=["Merchants"])
async def get_merchant(merchant_id: int, session: Session = Depends(get_session)):
    merchant = session.get(Merchants, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return merchant

@app.put("/api/merchants/{merchant_id}", response_model=MerchantOut, tags=["Merchants"])
async def update_merchant(
    merchant_id: int, 
    merchant_update: MerchantCreate, 
    current_user: Users = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    existing_merchant = session.get(Merchants, merchant_id)
    if not existing_merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Check if user is merchant admin
    if existing_merchant.admin_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this merchant"
        )
    
    # Don't allow changing admin_id to another user
    if merchant_update.admin_id and merchant_update.admin_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to transfer merchant ownership"
        )
    
    # Update merchant fields
    merchant_data = merchant_update.model_dump(exclude_unset=True)
    for key, value in merchant_data.items():
        setattr(existing_merchant, key, value)
    
    session.add(existing_merchant)
    session.commit()
    session.refresh(existing_merchant)
    return existing_merchant

@app.delete("/api/merchants/{merchant_id}", response_model=dict, tags=["Merchants"])
async def delete_merchant(
    merchant_id: int, 
    session: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
):
    merchant = session.get(Merchants, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Check if user is merchant admin
    if merchant.admin_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this merchant"
        )
    
    # Check if there are any products linked to this merchant
    product_count = session.exec(
        select(Products).where(Products.merchant_id == merchant_id)
    ).first()
    
    if product_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete merchant with existing products"
        )
    
    session.delete(merchant)
    session.commit()
    return {"ok": True, "message": "Merchant deleted successfully"}