from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List    
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import Session, Users, Orders, Products, Merchants, OrderItems
from sqlmodel import select
from datetime import datetime, timedelta
from schemas import UserCreate, UserOut, Token, OrderCreate, OrderItemCreate, ProductCreate, MerchantCreate
from db import engine, init_db

app = FastAPI()
init_db()




def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT Configuration
SECRET_KEY = "your-secret-key"  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_session():
    with Session(engine) as session:
        yield session
        

# Register endpoint
@app.post("/register", response_model=UserOut, tags=["User Management"])
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check if a user with the same email already exists
    statement = select(Users).where(Users.email == user.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password before saving
    hashed_password = get_password_hash(user.password)
    new_user = Users(
        full_name=user.full_name,
        email=user.email,
        password=hashed_password,
        gender=user.gender,
        date_of_birth=user.date_of_birth
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

# Login endpoint
@app.post("/login", response_model=Token, tags=["User Management"])
def login_user(email: str, password: str, session: Session = Depends(get_session)):
    # Retrieve user by email
    statement = select(Users).where(Users.email == email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify the provided password
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create and return an access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------------------
# Endpoints for Orders
# ------------------------------

@app.post("/orders", response_model=Orders, tags=["Orders"])
def create_order(order: OrderCreate, session: Session = Depends(get_session)):
    new_order = Orders(
        user_id=order.user_id,
        status=order.status,
        created_at=str(datetime.utcnow())
    )
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    return new_order

@app.get("/orders", response_model=List[Orders], tags=["Orders"])
def list_orders(session: Session = Depends(get_session)):
    orders = session.exec(select(Orders)).all()
    return orders

@app.get("/orders/{order_id}", response_model=Orders, tags=["Orders"])
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Orders, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# ------------------------------
# Endpoints for OrderItems
# ------------------------------

@app.post("/order_items", response_model=OrderItems, tags=["OrderItems"])
def create_order_item(item: OrderItemCreate, session: Session = Depends(get_session)):
    new_item = OrderItems(
        order_id=item.order_id,
        product_id=item.product_id,
        quantity=item.quantity
    )
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return new_item

@app.get("/order_items", response_model=List[OrderItems], tags=["OrderItems"])
def list_order_items(session: Session = Depends(get_session)):
    items = session.exec(select(    )).all()
    return items

@app.get("/order_items/{order_id}/{product_id}", response_model=OrderItems, tags=["OrderItems"])
def get_order_item(order_id: int, product_id: int, session: Session = Depends(get_session)):
    item = session.get(OrderItems, (order_id, product_id))
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    return item

# ------------------------------
# Endpoints for Products
# ------------------------------

@app.post("/products", response_model=Products, tags=["Products"])
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    new_product = Products(
        name=product.name,
        merchant_id=product.merchant_id,
        price=product.price,
        status=product.status,
        created_at=str(datetime.utcnow()),
        category_id=product.category_id
    )
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    return new_product

@app.get("/products", response_model=List[Products], tags=["Products"])
def list_products(session: Session = Depends(get_session)):
    products = session.exec(select(Products)).all()
    return products

@app.get("/products/{product_id}", response_model=Products, tags=["Products"])
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=Products, tags=["Products"])
def update_product(product_id: int, product: ProductCreate, session: Session = Depends(get_session)):
    existing_product = session.get(Products, product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_data = product.dict(exclude_unset=True)
    for key, value in product_data.items():
        setattr(existing_product, key, value)
    session.add(existing_product)
    session.commit()
    session.refresh(existing_product)
    return existing_product

@app.delete("/products/{product_id}", response_model=dict, tags=["Products"])
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(Products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"ok": True}

# ------------------------------
# Endpoints for Merchants
# ------------------------------

@app.post("/merchants", response_model=Merchants, tags=["Merchants"])
def create_merchant(merchant: MerchantCreate, session: Session = Depends(get_session)):
    new_merchant = Merchants(
        admin_id=merchant.admin_id,
        merchant_name=merchant.merchant_name,
        created_at=str(datetime.utcnow())
    )
    session.add(new_merchant)
    session.commit()
    session.refresh(new_merchant)
    return new_merchant

@app.get("/merchants", response_model=List[Merchants], tags=["Merchants"])
def list_merchants(session: Session = Depends(get_session)):
    merchants = session.exec(select(Merchants)).all()
    return merchants

@app.get("/merchants/{merchant_id}", response_model=Merchants, tags=["Merchants"])
def get_merchant(merchant_id: int, session: Session = Depends(get_session)):
    merchant = session.get(Merchants, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return merchant

@app.put("/merchants/{merchant_id}", response_model=Merchants, tags=["Merchants"])
def update_merchant(merchant_id: int, merchant: MerchantCreate, session: Session = Depends(get_session)):
    existing_merchant = session.get(Merchants, merchant_id)
    if not existing_merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    merchant_data = merchant.dict(exclude_unset=True)
    for key, value in merchant_data.items():
        setattr(existing_merchant, key, value)
    session.add(existing_merchant)
    session.commit()
    session.refresh(existing_merchant)
    return existing_merchant

@app.delete("/merchants/{merchant_id}", response_model=dict, tags=["Merchants"])
def delete_merchant(merchant_id: int, session: Session = Depends(get_session)):
    merchant = session.get(Merchants, merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    session.delete(merchant)
    session.commit()
    return {"ok": True}