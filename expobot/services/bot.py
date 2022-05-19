from datetime import datetime
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from services.calculations import floor_to_price
from models.level import Level, LevelModel, LevelStatus

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
        bot = BotWithDetails(
            **(await self.bot).dict(),
            orders=await self.get_orders(),
            levels=await self.get_levels(),
        )
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
        orders_scalars = (await self.session.execute(query)).scalars()
        return [Order.from_orm(order) for order in orders_scalars]

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
        if not await self.can_place_buy_order(floor):
            raise HTTPException(
                status_code=409,
                detail="Can't place buy order for this level",
            )
        level = await self._get_level(floor)

        try:
            exchange_order = self.exchange.place_buy_order(
                price=level.price, amount=amount
            )
        except Exception as e:
            self.stop(message=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        fee_data = exchange_order.get("fee")
        if fee_data is not None:
            fee = dict(
                cost=fee_data.get("cost"),
                currency=fee_data.get("currency"),
                rate=fee_data.get("rate"),
            )
        else:
            fee = dict(cost=None, currency=None, rate=None)

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
        self.session.add(order)
        level.buy_amount = order.amount
        level.buy_order_id = order.order_id
        level.buy_status = LevelStatus.OPEN
        await self.session.add(level)
        await self.session.commit()
        return Order.from_orm(order)

    ###########################################################################
    # level management
    ###########################################################################
    async def get_levels(self) -> list[Level]:
        """Get all levels"""
        query = select(LevelModel).where(LevelModel.bot_id == self.id)
        levels_scalars = (await self.session.execute(query)).scalars()
        levels = [Level.from_orm(level) for level in levels_scalars]
        # delete empty levels at the top and bottom
        while levels and levels[0].is_empty():
            levels.pop(0)
        while levels and levels[-1].is_empty():
            levels.pop()
        return levels

    async def _get_level(self, floor: int) -> LevelModel:
        """Get level"""
        query = select(LevelModel).where(
            LevelModel.bot_id == self.id, LevelModel.floor == floor
        )
        level = await self.session.execute(query).scalar_one_or_none()
        if level is not None:
            return LevelModel.from_orm(level)
        level = LevelModel(
            bot_id=self.id,
            floor=level,
            price=floor_to_price(
                floor=level,
                level_height=self.bot.total_level_height,
                level_0_price=self.bot.level_0_price,
            ),
        )
        self.session.add(level)
        await self.session.commit()
        await self.session.refresh(level)
        return level

    ###########################################################################
    # bot control
    ###########################################################################
    async def tick(self, nonce: int) -> None:
        """Handle tick"""
        print(f">>>>>> tick {datetime.fromtimestamp(nonce/1000)}")

    async def start(self) -> Bot:
        """Start bot"""
        bot = await self.bot
        if bot.status == BotStatus.STOPPED:
            bot.status = BotStatus.RUNNING
            await self.session.add(bot)
            await self.session.commit()
            await self.session.refresh(bot)
        return Bot.from_orm(bot)

    async def stop(self, message: str = None) -> Bot:
        """Stop bot"""
        bot = await self.bot
        if bot.status == BotStatus.RUNNING:
            bot.status = BotStatus.STOPPED
            bot.message = message
            await self.session.add(bot)
            await self.session.commit()
            await self.session.refresh(bot)
        return Bot.from_orm(bot)
