from requests import session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from db import get_session
from schemas.enums import BotStatus
from models.bot import Bot
from schemas.bot import Bot, BotCreate
from services.exchange import exchanges_manager
from sqlmodel import select


class BotService:
    def __init__(self, id: int, session: AsyncSession = Depends(get_session)):
        self.id = id
        self.session = session
        # TODO: fix this: self.exchange = exchanges[self.bot.exchange_account]

    async def get_bot(self) -> Bot:
        """Get bot by id"""
        bot = (
            await self.session.execute(select(Bot).where(Bot.id == self.id))
        ).scalar_one_or_none()
        if bot is None:
            raise HTTPException(
                status_code=404, detail=f"Bot with id={self.id} not found"
            )
        return bot

    @staticmethod
    async def get_bots(
        session: AsyncSession, status: BotStatus | None = None
    ) -> list[Bot]:
        """Get all bot ids"""
        query = select(Bot)
        if status is not None:
            query = query.where(Bot.status == status)
        bots = (await session.execute(query))
        return list(bots.scalars())


    @staticmethod
    async def create_bot(session: AsyncSession, bot_data: BotCreate) -> Bot:
        """Create bot"""

        if (await session.execute(select(Bot).where(Bot.name == bot_data.name))).one_or_none():
            raise HTTPException(
                status_code=409, detail="Bot with the same name already exists"
            )
        exchange = exchanges_manager[bot_data.exchange_account]
        symbol_info = exchange.fetch_symbol_info(bot_data.symbol)
        taker = symbol_info["taker"]
        maker = symbol_info["maker"]
        total_level_height=bot_data.level_height + taker + maker
        bot = Bot(
            **bot_data.dict(),
            status=BotStatus.STOPPED,
            taker=taker,
            maker=maker,
            total_level_height=total_level_height,
            last_level=0,
            last_price=0,
        )
        print('>>>>>>>>>>>>>>>>>', bot)
        session.add(bot)
        await session.commit()
        await session.refresh(bot)
        return bot


    # async def delete_bot(self) -> None:
    #     """Delete bot by id"""
    #     bot_orm = await self.__get()
    #     await bot_orm.delete()
