from fastapi import Depends, HTTPException
from sqlmodel import select, Session

from ..models.bot import Bot, BotCreate, BotModel, BotStatus, BotWithDetails
from ..models.level import Level, LevelModel
from ..models.order import Order, OrderModel, OrderSide, OrderStatus
from ..services.db import get_session
from ..services.exchange.manager import exchanges_manager


class BotsManager:
    def __init__(
        self,
        bot_id: int | None = None,
        session: Session = Depends(get_session),
    ):
        self.id = bot_id
        self.session = session

    def get_bots(self, status: BotStatus | None = None) -> list[Bot]:
        """Get all bots"""

        query = select(BotModel)
        if status is not None:
            query = query.where(BotModel.status == status)
        bots = self.session.exec(query).all()
        return [Bot.from_orm(b) for b in bots]

    def get_bot(self) -> Bot:
        """Get bot by id"""
        bot = (
            self.session.exec(select(BotModel).where(BotModel.id == self.id))
        ).one_or_none()
        if bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        return Bot.from_orm(bot)

    def get_bot_with_details(self) -> BotWithDetails:
        """Get bot by id with orders and levels"""
        bot = self.get_bot()
        orders = self.get_orders()
        levels = self.get_levels()
        bot = BotWithDetails(**bot.dict(), orders=orders, levels=levels)
        return bot

    def create_bot(self, bot_data: BotCreate) -> Bot:
        """Create bot"""
        exchange = exchanges_manager.get(bot_data.exchange_account)
        symbol_info = exchange.fetch_market(bot_data.symbol)
        taker = symbol_info["taker"]
        maker = symbol_info["maker"]
        total_level_height = 1 + bot_data.level_height + taker + maker
        bot = BotModel(
            **bot_data.dict(),
            status=BotStatus.RUNNING,  # TODO: !!! must be STOPPED
            taker=taker,
            maker=maker,
            total_level_height=total_level_height,
            last_floor=0,
            last_price=0,
        )
        self.session.add(bot)
        self.session.commit()
        self.session.refresh(bot)
        return Bot.from_orm(bot)

    def delete_bot(self) -> None:
        """Delete bot by id"""
        self.session.delete(BotModel, self.id)
        self.session.commit()

    def get_orders(
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
        orders = self.session.execute(query).all()
        result = [Order.from_orm(order) for order in orders]
        return result

    def get_levels(self) -> list[Level]:
        """Get all levels"""
        query = (
            select(LevelModel)
            .where(LevelModel.bot_id == self.id)
            .order_by(LevelModel.floor)
        )
        levels = self.session.execute(query).all()
        levels = [Level.from_orm(level) for level in levels]
        # delete empty levels at the top and bottom
        while levels and levels[0].is_empty():
            levels.pop(0)
        while levels and levels[-1].is_empty():
            levels.pop()
        return levels
