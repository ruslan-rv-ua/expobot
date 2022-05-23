from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.level import Level, LevelModel

from models.bot import Bot, BotCreate, BotModel, BotStatus, BotWithDetails
from models.order import Order, OrderModel, OrderSide, OrderStatus
from .db import get_session
from .exchange.manager import exchanges_manager


class BotsManager:
    def __init__(
        self, bot_id: int | None = None, session: AsyncSession = Depends(get_session)
    ):
        self.id = bot_id
        self.session = session

    async def get_bots(self, status: BotStatus | None = None) -> list[Bot]:
        """Get all bots"""

        query = select(BotModel)
        if status is not None:
            query = query.where(BotModel.status == status)
        bots = await self.session.execute(query)
        return [Bot.from_orm(b) for b in bots.scalars()]

    async def get_bot(self) -> Bot:
        """Get bot by id"""
        bot_scalar = (
            await self.session.execute(select(BotModel).where(BotModel.id == self.id))
        ).scalar_one_or_none()
        if bot_scalar is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        return Bot.from_orm(bot_scalar)

    async def get_bot_with_details(self) -> BotWithDetails:
        """Get bot by id with orders and levels"""
        bot = await self.get_bot()
        orders = await self.get_orders()
        levels = await self.get_levels()
        bot = BotWithDetails(**bot.dict(), orders=orders, levels=levels)
        return bot

    async def create_bot(self, bot_data: BotCreate) -> Bot:
        """Create bot"""
        name = f"{bot_data.trade_amount}x " \
            f"{bot_data.symbol} " \
            f"~ {round(bot_data.level_height * 100, 2)}% " \
            f"@ {bot_data.exchange_account}"
        if (
            await self.session.execute(
                select(BotModel).where(BotModel.name == name)
            )
        ).one_or_none():
            raise HTTPException(
                status_code=409, detail="Bot with the same parameters already exists"
            )
        exchange = exchanges_manager.get(bot_data.exchange_account)
        symbol_info = exchange.fetch_symbol_info(bot_data.symbol)
        taker = symbol_info["taker"]
        maker = symbol_info["maker"]
        total_level_height = 1 + bot_data.level_height + taker + maker
        bot = BotModel(
            **bot_data.dict(),
            status=BotStatus.STOPPED,
            name=name,
            taker=taker,
            maker=maker,
            total_level_height=total_level_height,
            last_floor=0,
            last_price=0,
        )
        self.session.add(bot)
        await self.session.commit()
        await self.session.refresh(bot)
        return Bot.from_orm(bot)

    async def delete_bot(self) -> None:
        """Delete bot by id"""
        await self.session.delete(await self.bot)
        await self.session.commit()

    async def get_orders(
        self, side: OrderSide | None = None, status: OrderStatus | None = None
    ) -> list[Order]:
        """Get all orders for bot"""
        query = (
            select(OrderModel)
            .where(OrderModel.bot_id == self.id)
            .order_by(OrderModel.timestamp)
        )
        if side is not None:
            query = query.where(Order.side == side)
        if status is not None:
            query = query.where(Order.status == status)
        orders_scalars = (await self.session.execute(query)).scalars()
        result = [Order.from_orm(order) for order in orders_scalars]
        return result

    async def get_levels(self) -> list[Level]:
        """Get all levels"""
        query = (
            select(LevelModel)
            .where(LevelModel.bot_id == self.id)
            .order_by(LevelModel.floor)
        )
        levels_scalars = (await self.session.execute(query)).scalars()
        levels = [Level.from_orm(level) for level in levels_scalars]
        # delete empty levels at the top and bottom
        while levels and levels[0].is_empty():
            levels.pop(0)
        while levels and levels[-1].is_empty():
            levels.pop()
        return levels
