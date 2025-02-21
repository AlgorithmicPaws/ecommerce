from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlmodel import Field, Session, SQLModel, create_engine, select
from passlib.context import CryptContext

# Set up a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(index=True, nullable=False, sa_column_kwargs={"unique": True})
    password: str = Field()  # This will store the hashed password.
    role: str = Field(default="user")

# Pydantic models for user input
class UserCreate(SQLModel):
    name: str
    email: str
    password: str

class UserLogin(SQLModel):
    email: str
    password: str

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    create_db_and_tables()

@app.post("/register", response_model=User,  tags=["User Management"])
def register_user(user: UserCreate, session: SessionDep):
    # Check if a user with the same email already exists
    statement = select(User).where(User.email == user.email)
    result = session.exec(statement)
    existing_user = result.first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password before saving
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post("/login", tags=["User Management"])
def login_user(user: UserLogin, session: SessionDep ):
    statement = select(User).where(User.email == user.email)
    result = session.exec(statement)
    db_user = result.first()
    # Check if the user exists and the provided password is correct.
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    # In a real application you would return a JWT or session token here.
    return {"message": "Login successful"}

@app.get("/users", tags=["Usuarios"])
def get_users():
    return {"message": "GET: List all users"}

@app.get("/users/{user_id}", tags=["Usuarios"])
def get_user(user_id: int):
    return {"message": f"GET: Details of user {user_id}"}

@app.put("/users/{user_id}", tags=["Usuarios"])
def update_user(user_id: int):
    return {"message": f"PUT: Update user {user_id}"}

@app.delete("/users/{user_id}", tags=["Usuarios"])
def delete_user(user_id: int):
    return {"message": f"DELETE: Delete user {user_id}"}


# ------------------------
# Carrito de compras: todos (GET, POST, PUT, DELETE)
# ------------------------
@app.get("/cart", tags=["Carrito de compras"])
def get_cart():
    return {"message": "GET: Retrieve shopping cart"}

@app.post("/cart", tags=["Carrito de compras"])
def add_to_cart():
    return {"message": "POST: Add item to shopping cart"}

@app.put("/cart/{item_id}", tags=["Carrito de compras"])
def update_cart(item_id: int):
    return {"message": f"PUT: Update cart item {item_id}"}

@app.delete("/cart/{item_id}", tags=["Carrito de compras"])
def delete_cart(item_id: int):
    return {"message": f"DELETE: Remove cart item {item_id}"}


# ------------------------
# Sistema de recomendación: get
# ------------------------
@app.get("/recommendations", tags=["Sistema de recomendación"])
def get_recommendations():
    return {"message": "GET: Get recommendations"}


# ------------------------
# Vendedor: todos menos POST (GET, PUT, DELETE)
# ------------------------
@app.get("/seller", tags=["Vendedor"])
def get_sellers():
    return {"message": "GET: List all sellers"}

@app.get("/seller/{seller_id}", tags=["Vendedor"])
def get_seller(seller_id: int):
    return {"message": f"GET: Get seller {seller_id}"}

@app.put("/seller/{seller_id}", tags=["Vendedor"])
def update_seller(seller_id: int):
    return {"message": f"PUT: Update seller {seller_id}"}

@app.delete("/seller/{seller_id}", tags=["Vendedor"])
def delete_seller(seller_id: int):
    return {"message": f"DELETE: Delete seller {seller_id}"}


# ------------------------
# Tienda (filtro): todos (GET, POST, PUT, DELETE)
# ------------------------
@app.get("/store", tags=["Tienda"])
def get_store():
    return {"message": "GET: Retrieve store items (with filtering)"}

@app.post("/store", tags=["Tienda"])
def create_store_item():
    return {"message": "POST: Create store item"}

@app.put("/store/{item_id}", tags=["Tienda"])
def update_store_item(item_id: int):
    return {"message": f"PUT: Update store item {item_id}"}

@app.delete("/store/{item_id}", tags=["Tienda"])
def delete_store_item(item_id: int):
    return {"message": f"DELETE: Delete store item {item_id}"}


# ------------------------
# Pagos: por confirmar
# ------------------------
@app.get("/payments", tags=["Pagos"])
def get_payments():
    return {"message": "GET: Payment endpoints - to be confirmed"}

@app.post("/payments", tags=["Pagos"])
def create_payment():
    return {"message": "POST: Payment endpoints - to be confirmed"}


# ------------------------
# Pedidos: lo que me comprometo a pagar - todos (GET, POST, PUT, DELETE)
# ------------------------
@app.get("/orders", tags=["Pedidos"])
def get_orders():
    return {"message": "GET: List all orders"}

@app.post("/orders", tags=["Pedidos"])
def create_order():
    return {"message": "POST: Create an order"}

@app.get("/orders/{order_id}", tags=["Pedidos"])
def get_order(order_id: int):
    return {"message": f"GET: Get order {order_id}"}

@app.put("/orders/{order_id}", tags=["Pedidos"])
def update_order(order_id: int):
    return {"message": f"PUT: Update order {order_id}"}

@app.delete("/orders/{order_id}", tags=["Pedidos"])
def delete_order(order_id: int):
    return {"message": f"DELETE: Delete order {order_id}"}


# ------------------------
# Facturación: registro del pago contable: post y get
# ------------------------
@app.get("/billing", tags=["Facturación"])
def get_billing():
    return {"message": "GET: Retrieve billing records"}

@app.post("/billing", tags=["Facturación"])
def create_billing():
    return {"message": "POST: Create a billing record"}


# ------------------------
# Productos (inventario, filtro): todos (GET, POST, PUT, DELETE)
# ------------------------
@app.get("/products", tags=["Productos"])
def get_products():
    return {"message": "GET: List all products"}

@app.post("/products", tags=["Productos"])
def create_product():
    return {"message": "POST: Create a product"}

@app.get("/products/{product_id}", tags=["Productos"])
def get_product(product_id: int):
    return {"message": f"GET: Get product {product_id}"}

@app.put("/products/{product_id}", tags=["Productos"])
def update_product(product_id: int):
    return {"message": f"PUT: Update product {product_id}"}

@app.delete("/products/{product_id}", tags=["Productos"])
def delete_product(product_id: int):
    return {"message": f"DELETE: Delete product {product_id}"}