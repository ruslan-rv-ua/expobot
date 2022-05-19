from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from models.bot import Bot, BotCreate, BotModel, BotStatus, BotWithDetails
from models.order import Order, OrderModel, OrderSide, OrderStatus
from .db import get_session
from .exchange import Exchange, exchanges_manager


class BotsManager:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def get_bots(self, status: BotStatus | None = None) -> list[Bot]:
        """Get all bots"""
        query = select(BotModel)
        if status is not None:
            query = query.where(BotModel.status == status)
        bots = await self.session.execute(query)
        return [Bot.from_orm(b) for b in bots.scalars()]

    async def create_bot(self, bot_data: BotCreate) -> Bot:
        """Create bot"""

        if (
            await self.session.execute(
                select(BotModel).where(BotModel.name == bot_data.name)
            )
        ).one_or_none():
            raise HTTPException(
                status_code=409, detail="Bot with the same name already exists"
            )
        exchange = exchanges_manager[bot_data.exchange_account]
        symbol_info = exchange.fetch_symbol_info(bot_data.symbol)
        taker = symbol_info["taker"]
        maker = symbol_info["maker"]
        total_level_height = bot_data.level_height + taker + maker
        bot = BotModel(
            **bot_data.dict(),
            status=BotStatus.STOPPED,
            taker=taker,
            maker=maker,
            total_level_height=total_level_height,
            last_level=0,
            last_price=0,
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        return Bot.from_orm(bot)


class BotRunner:
    def __init__(self, bot_id: int, session: AsyncSession = Depends(get_session)):
        self.id = bot_id
        self.session = session
        self._bot = None
        self._exchange = None

    @property
    async def bot(self) -> BotModel:
        """Get bot from database"""
        if self._bot is None:
            self._bot = (
                await self.session.execute(
                    select(BotModel).where(BotModel.id == self.id)
                )
            ).scalar_one_or_none()
            if self._bot is None:
                raise HTTPException(
                    status_code=404, detail=f"Bot with id={self.id} not found"
                )
        return self._bot

    @property
    def exchange(self) -> "Exchange":
        if self._exchange is None:
            self._exchange = exchanges_manager[self.bot.exchange_account]
        return self._exchange

    async def get_bot_with_details(self) -> BotWithDetails:
        """Get bot by id"""
        bot = BotWithDetails(**(await self.bot).dict(), orders=await self.get_orders())
        return bot

    async def delete_bot(self) -> None:
        """Delete bot by id"""
        await self.session.delete(await self.bot)
        await self.session.commit()

    ###########################################################################
    # order management
    ###########################################################################
    async def get_orders(
        self, side: OrderSide | None = None, status: OrderStatus | None = None
    ) -> list[Order]:
        """Get all orders for bot"""
        query = select(OrderModel).where(OrderModel.bot_id == self.id)
        if side is not None:
            query = query.where(Order.side == side)
        if status is not None:
            query = query.where(Order.status == status)
        orders = await self.session.execute(query)
        return [Order.from_orm(order) for order in orders.scalars()]


    ###########################################################################
    # tick management
    ###########################################################################
    async def tick(self, nonce:int) -> None:
        """Handle tick"""
        print(f">>>>>> tick {nonce}")
