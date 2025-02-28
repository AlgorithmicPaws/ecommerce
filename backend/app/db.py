from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = "postgresql://sergio:dinosaurio_cientifico@localhost:5432/ecommerce"
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
    