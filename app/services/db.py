from sqlmodel import SQLModel, Session, create_engine

from app import config

connect_args = {"check_same_thread": False}
engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)


def get_session() -> Session:
    with Session(engine) as session:
        yield session


def init_db():
    # uncomment next line to drop all tables
    # SQLModel.metadata.drop_all
    SQLModel.metadata.create_all
