from logging import getLogger
from app.models.bot import BotModel
from app.models.order import Order, OrderSide, OrderStatus
from app.services.order import OrdersRunner
from .db import SessionLocal
from ..models.level import LevelModel, LevelStatus

from . import calculations

from sqlmodel import select


class LevelsRunner:
    def __init__(self, bot: BotModel, orders: OrdersRunner):
        self.bot = bot
        self.orders = orders
        self.logger = getLogger("bot_runner")

    def price_to_floor(self, price: float) -> int:
        """Convert price to floor"""
        return calculations.price_to_floor(
            price=price,
            level_height=self.bot.total_level_height,
            level_0_price=self.bot.level_0_price,
        )

    def floor_to_price(self, floor: int) -> float:
        """Convert floor to price"""
        return calculations.floor_to_price(
            floor=floor,
            level_height=self.bot.total_level_height,
            level_0_price=self.bot.level_0_price,
        )

    async def get_list(
        self,
        buy_status: LevelStatus | None = None,
        sell_status: LevelStatus | None = None,
    ) -> list[LevelModel]:
        """Get list of levels"""
        async with SessionLocal() as session:
            query = select(LevelModel).where(LevelModel.bot_id == self.bot.id)
            if buy_status is not None:
                query = query.where(LevelModel.buy_status == buy_status)
            if sell_status is not None:
                query = query.where(LevelModel.sell_status == sell_status)
            query = query.order_by(LevelModel.floor)
            result = await session.execute(query)
        levels_list = list(result.scalars())
        while levels_list and levels_list[0].is_empty():
            levels_list.pop(0)
        while levels_list and levels_list[-1].is_empty():
            levels_list.pop()
        return levels_list

    async def get_mapping(self) -> dict[int, LevelModel]:
        """Get mapping of levels"""
        levels_list = await self.get_list()
        mapping = {level.floor: level for level in levels_list}
        return mapping

    async def update(self):
        """Update levels"""
        await self.orders.update_open_orders()

        async with SessionLocal() as session:
            # update open buy orders
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot.id,
                LevelModel.buy_status == LevelStatus.OPEN,
            )
            result = await session.execute(query)
            buy_levels = result.scalars()
            for buy_level in buy_levels:
                buy_order = await self.orders.get(buy_level.buy_order_id)
                if buy_order.status == OrderStatus.CLOSED:
                    buy_level.buy_status = LevelStatus.CLOSED
                    session.add(buy_level)

            # update open sell orders
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot.id,
                LevelModel.sell_status == LevelStatus.OPEN,
            )
            result = await session.execute(query)
            sell_levels = result.scalars()
            for sell_level in sell_levels:
                sell_order = await self.orders.get(sell_level.sell_order_id)
                if sell_order.status == OrderStatus.CLOSED:
                    sell_level.status = LevelStatus.CLOSED
                    session.add(sell_level)

            await session.commit()
        self.logger.debug("Levels updated")

    ###############################################################################

    async def clear_levels(self, floors: list[int]) -> None:
        """Clear levels"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor.in_(floors),
                )
            )
            for level in result.scalars():
                level.status = LevelStatus.NONE
                level.order_id = None
                level.amount = None
                session.add(level)
            await session.commit()

    async def clear_buy_level(self, floor: int) -> None:
        """Clear buy level"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            )
            level = result.scalar_one_or_none()
            if level is None:
                raise Exception(f"Level {floor} not found")

            level.buy_status = LevelStatus.NONE
            level.buy_order_id = None
            level.amount = None
            session.add(level)
            await session.commit()

    async def clear_sell_level(self, floor: int) -> None:
        """Clear sell level"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            )
            level = result.scalar_one_or_none()
            if level is None:
                raise Exception(f"Level {floor} not found")

            level.sell_status = LevelStatus.NONE
            level.sell_order_id = None
            level.amount = None
            session.add(level)
            await session.commit()

    async def buy_level(self, floor: int, amount: float):
        """Buy level"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            )
            level = result.scalar_one_or_none()
            if level is None:
                level = LevelModel(
                    bot_id=self.bot.id,
                    floor=floor,
                    price=self.floor_to_price(floor),
                )
                session.add(level)
                await session.commit()
                await session.refresh(level)

        if level.buy_status != LevelStatus.NONE:
            raise Exception(f"Level {floor} is not empty")

        order = await self.orders.place_order(
            side=OrderSide.BUY, amount=amount, price=level.price
        )

        async with SessionLocal() as session:
            level.buy_status = LevelStatus.OPEN
            level.buy_order_id = order.order_id
            level.amount = order.amount
            session.add(level)
            await session.commit()

    async def sell_level(self, floor: int, amount: float):
        """Sell level"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            )
            level = result.scalar_one_or_none()
            if level is None:
                level = LevelModel(
                    bot_id=self.bot.id,
                    floor=floor,
                    price=self.floor_to_price(floor),
                )
                session.add(level)
                await session.commit()
                await session.refresh(level)
        if level.sell_status != LevelStatus.NONE:
            raise Exception(f"Level {floor} is not empty")

        order = await self.orders.place_order(
            side=OrderSide.SELL, amount=amount, price=level.price
        )

        async with SessionLocal() as session:
            level.sell_status = LevelStatus.OPEN
            level.sell_order_id = order.order_id
            level.amount = order.amount
            session.add(level)
            await session.commit()
