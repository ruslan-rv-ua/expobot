from sqlmodel import Session, SQLModel, create_engine

from . import config

# from .models.bot import BotModel  # noqa
# from .models.level import LevelModel  # noqa
# from .models.order import OrderModel  # noqa

connect_args = {"check_same_thread": False}
engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)


def get_session() -> Session:
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    # uncomment next line to drop all tables
    # SQLModel.metadata.drop_all
    SQLModel.metadata.create_all(engine)
