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

    async def _get_level(self, floor: int) -> LevelModel:
        """Get level"""
        async with SessionLocal() as session:
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot.id, LevelModel.floor == floor
            )
            level = (await session.execute(query)).scalar_one_or_none()
            if level is not None:
                return level
        level = LevelModel(
            bot_id=self.bot.id,
            floor=floor,
            price=self.floor_to_price(floor),  # TODO !!!
        )
        session.add(level)
        await session.commit()
        await session.refresh(level)
        return level

    async def update(self):
        """Update levels"""
        await self.orders.update_open_orders()

        async with SessionLocal() as session:
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot.id,
                LevelModel.buy_status == LevelStatus.OPEN,
            )
            result = await session.execute(query)
            levels_to_check = list(result.scalars())
            for level in levels_to_check:
                order = await self.orders.get(level.buy_order_id)
                if order.status == OrderStatus.CLOSED:
                    level.buy_status = LevelStatus.CLOSED
                    session.add(level)
            await session.commit()

            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot.id,
                LevelModel.sell_status == LevelStatus.OPEN,
            )
            result = await session.execute(query)
            levels_to_check = list(result.scalars())
            for level in levels_to_check:
                order = await self.orders.get(level.sell_order_id)
                if order.status == OrderStatus.CLOSED:
                    level.sell_status = LevelStatus.CLOSED
                    session.add(level)

            await session.commit()

    async def can_place_buy_order(self, floor: int) -> bool:
        level = await self._get_level(floor)
        if level.buy_status != LevelStatus.NONE:
            return False
        level_up = await self._get_level(floor + 1)
        if level_up.sell_status not in (LevelStatus.NONE, LevelStatus.CLOSED):
            return False
        return True

    async def can_place_sell_order(self, floor: int) -> bool:
        level = await self._get_level(floor)
        if level.sell_status != LevelStatus.NONE:
            return False
        return True

    async def place_order(
        self, floor: int, side: OrderSide, amount: float
    ) -> Order:
        """Place buy order"""
        # TODO: make exeption
        match side:
            case OrderSide.BUY:
                if not await self.can_place_buy_order(floor):
                    raise Exception(
                        f"Can't place buy order for this level: {floor}",
                    )
            case OrderSide.SELL:
                if not await self.can_place_sell_order(floor):
                    raise Exception(
                        f"Can't place sell order for this level: {floor}",
                    )

        order = await self.orders.place_order(
            side=side,
            amount=amount,
            price=self.floor_to_price(floor),  # TODO !!!
        )

        level = await self._get_level(floor)
        async with SessionLocal() as session:
            if side == OrderSide.BUY:
                level.set_buy_order(order_id=order.order_id, amount=order.amount)
            elif side == OrderSide.SELL:
                level.set_sell_order(order_id=order.order_id, amount=order.amount)
            session.add(level)
            await session.commit()
        return order

    async def _cancel_opened_buy_order_at_level(self, floor: int) -> LevelModel:
        level = await self._get_level(floor)
        await self.orders.cancel_order(order_id=level.buy_order_id)
        level = await self._get_level(floor)
        async with SessionLocal() as session:
            level.clear_buy_order()
            session.add(level)
            await session.commit()
