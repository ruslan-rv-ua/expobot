from logging import getLogger

from sqlmodel import select, Session

from app.db import engine
from app.models.bot import BotModel
from app.models.order import OrderSide, OrderStatus
from app.services.order import OrdersRunner

from ..models.level import LevelModel, LevelStatus
from . import calculations


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

    def get_list(
        self,
        buy_status: LevelStatus | None = None,
        sell_status: LevelStatus | None = None,
    ) -> list[LevelModel]:
        """Get list of levels"""
        query = select(LevelModel).where(LevelModel.bot_id == self.bot.id)
        if buy_status is not None:
            query = query.where(LevelModel.buy_status == buy_status)
        if sell_status is not None:
            query = query.where(LevelModel.sell_status == sell_status)
        query = query.order_by(LevelModel.floor)
        with Session(engine) as session:
            levels_list = session.exec(query).all()
        while levels_list and levels_list[0].is_empty():
            levels_list.pop(0)
        while levels_list and levels_list[-1].is_empty():
            levels_list.pop()
        return levels_list

    def get_mapping(
        self,
        buy_status: LevelStatus | None = None,
        sell_status: LevelStatus | None = None,
    ) -> dict[int, LevelModel]:
        """Get mapping of levels"""
        levels_list = self.get_list(
            buy_status=buy_status, sell_status=sell_status
        )
        mapping = {level.floor: level for level in levels_list}
        return mapping

    def update(self):
        """Update levels"""
        self.orders.update_open_orders()

        with Session(engine) as session:
            # update open buy orders
            buy_levels = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.buy_status == LevelStatus.OPEN,
                )
            ).all()
            for buy_level in buy_levels:
                buy_order = self.orders.get(buy_level.buy_order_id)
                if buy_order.status == OrderStatus.CLOSED:
                    buy_level.buy_status = LevelStatus.CLOSED
                    session.add(buy_level)

            # update open sell orders
            sell_levels = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.sell_status == LevelStatus.OPEN,
                )
            ).all()
            for sell_level in sell_levels:
                sell_order = self.orders.get(sell_level.sell_order_id)
                if sell_order.status == OrderStatus.CLOSED:
                    sell_level.sell_status = LevelStatus.CLOSED
                    session.add(sell_level)

            session.commit()

        self.logger.debug("Levels updated")

    ###########################################################################

    def clear_buy_level(self, floor: int) -> None:
        """Clear buy level"""
        with Session(engine) as session:
            level = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            ).one_or_none()
            assert (
                level is not None
            ), f"Level {floor} not found, can't clear buy level"

            level.buy_status = LevelStatus.NONE
            level.buy_order_id = None
            level.buy_amount = None
            session.add(level)
            session.commit()

    def clear_sell_level(self, floor: int) -> None:
        """Clear sell level"""
        with Session(engine) as session:
            level = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            ).one_or_none()
            assert (
                level is not None
            ), f"Level {floor} not found, can't clear sell level"

            level.sell_status = LevelStatus.NONE
            level.sell_order_id = None
            level.sell_amount = None
            session.add(level)
            session.commit()

    def buy_level(self, floor: int, amount: float) -> LevelModel:
        """Buy level"""
        with Session(engine) as session:
            level = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            ).one_or_none()
            if level is None:
                level = LevelModel(
                    bot_id=self.bot.id,
                    floor=floor,
                    price=self.floor_to_price(floor),
                )
                session.add(level)
                session.commit()
                session.refresh(level)

            assert (
                level.buy_status == LevelStatus.NONE
            ), f"Level {level!r} is not empty, can't buy"

            order = self.orders.place_order(
                side=OrderSide.BUY, amount=amount, price=level.price
            )

        level.buy_status = LevelStatus.OPEN
        level.buy_order_id = order.order_id
        level.buy_amount = order.amount
        session.add(level)
        session.commit()

    def sell_level(self, floor: int, amount: float):
        """Sell level"""
        with Session(engine) as session:
            level = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            ).one_or_none()
            if level is None:
                level = LevelModel(
                    bot_id=self.bot.id,
                    floor=floor,
                    price=self.floor_to_price(floor),
                )
                session.add(level)
                session.commit()
                session.refresh(level)
            assert (
                level.sell_status == LevelStatus.NONE
            ), f"Level {level!r} is not empty, can't sell"

            order = self.orders.place_order(
                side=OrderSide.SELL, amount=amount, price=level.price
            )

            level.sell_status = LevelStatus.OPEN
            level.sell_order_id = order.order_id
            level.sell_amount = order.amount
            session.add(level)
            session.commit()

    def cancel_buy_level(self, floor: int):
        """Cancel buy level"""
        with Session(engine) as session:
            level = session.exec(
                select(LevelModel).where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.floor == floor,
                )
            ).one_or_none()
            assert (
                level is not None
            ), f"Level {level!r} not found, can't cancel buy level"

            self.logger.debug(f"Canceling buy level {level!r}")
            assert (
                level.buy_status == LevelStatus.OPEN
            ), f"Level {level!r} is not open, can't cancel buy"

            self.orders.cancel_order(level.buy_order_id)

            level.buy_status = LevelStatus.NONE
            level.buy_order_id = None
            level.buy_amount = None
            session.add(level)
            session.commit()
            session.refresh(level)
            self.logger.debug(f"Buy {level!r} canceled")
