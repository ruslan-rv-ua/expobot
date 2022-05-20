from datetime import datetime
from sqlmodel import select
from services.calculations import floor_to_price
from models.level import LevelModel, LevelStatus

from models.bot import Bot, BotModel, BotStatus
from models.order import Order, OrderModel, OrderSide, OrderStatus
from .db import Session
from .exchange import Exchange


class BotRunner:
    def __init__(self, bot_data: Bot, exchange: Exchange) -> None:
        self.bot_data = bot_data
        self.exchange = exchange

    async def _get_bot(self) -> BotModel:
        """Get bot"""
        bot = await self.session.query(BotModel).where(
            BotModel.id == self.bot_data.id
        ).scalar_one_or_none()
        if bot is None:
            raise Exception(f"Bot {self.bot_data.id} not found")
        return bot

    ###########################################################################
    # level management
    ###########################################################################

    async def _get_level(self, floor: int) -> LevelModel:
        """Get level"""
        async with Session() as session:
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot_data.id, LevelModel.floor == floor
            )
            level = await session.execute(query).scalar_one_or_none()
            if level is not None:
                return level
        level = LevelModel(
            bot_id=self.bot_data.id,
            floor=floor,
            price=floor_to_price(
                floor=floor,
                level_height=self.bot_data.total_level_height,
                level_0_price=self.bot_data.level_0_price,
            )
        )
        session.add(level)
        await session.commit()
        await session.refresh(level)
        return level

    ###########################################################################
    # order management
    ###########################################################################

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

    async def place_buy_order(self, floor: int, amount: float) -> Order:
        """Place buy order"""
        # TODO: make exeption
        if not await self.can_place_buy_order(floor):
            raise Exception(
                f"Can't place buy order for this level: {floor}",
            )
        level = await self._get_level(floor)

        try:
            exchange_order = self.exchange.place_buy_order(
                price=level.price, amount=amount
            )
        except Exception as e:
            self.stop(message=str(e))
            raise Exception(status_code=500, detail=str(e))
        fee_data = exchange_order.get("fee")
        if fee_data is not None:
            fee = dict(
                cost=fee_data.get("cost"),
                currency=fee_data.get("currency"),
                rate=fee_data.get("rate"),
            )
        else:
            fee = dict(cost=None, currency=None, rate=None)

        async with Session as session:
            order = OrderModel(
                bot_id=self.id,
                order_id=exchange_order["id"],
                timestamp=exchange_order.get("timestamp"),
                status=OrderStatus.OPEN,
                side=OrderSide.BUY,
                price=exchange_order.get("price"),
                average=exchange_order.get("average"),
                amount=exchange_order.get("amount"),
                cost=exchange_order.get("cost"),
                **fee,
            )
            session.add(order)
            level.buy_amount = order.amount
            level.buy_order_id = order.order_id
            level.buy_status = LevelStatus.OPEN
            session.add(level)
            await session.commit()
            await session.refresh(order)
            return order

    # TODO: add place sell order
    # TODO: add cancel order


    ###########################################################################
    # bot control
    ###########################################################################
    async def tick(self, nonce: int) -> None:
        """Handle tick"""
        print(f">>>>>> tick {datetime.fromtimestamp(nonce/1000)}")

    async def start(self) -> Bot:
        """Start bot"""
        async with Session() as session:
            bot = await self._get_bot()
            if bot.status == BotStatus.STOPPED:
                bot.status = BotStatus.RUNNING
                session.add(bot)
                await session.commit()
                await session.refresh(bot)
                return bot
            else:
                raise Exception(f"Bot {bot.id} already running")

    async def stop(self, message: str = None) -> Bot:
        """Stop bot"""
        async with Session() as session:
            bot = await self._get_bot()
            if bot.status == BotStatus.RUNNING:
                bot.status = BotStatus.STOPPED
                bot.message = message
                session.add(bot)
                await session.commit()
                await session.refresh(bot)
                return bot
            else:
                raise Exception(f"Bot {bot.id} already stopped")
