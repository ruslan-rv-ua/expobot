from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
Session: AsyncSession = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=True
)


async def get_session() -> AsyncSession:
    async with Session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        # uncomment next line to drop all tables
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
