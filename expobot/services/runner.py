from multiprocessing.connection import wait
from sqlmodel import select
from services.calculations import floor_to_price, price_to_floor
from models.level import LevelModel, LevelStatus

from models.bot import Bot, BotModel, BotStatus
from models.order import Order, OrderSide, OrderStatus
from .db import Session
from .exchange.base import ExchangeBase
from .order import Orders


class BotRunner:
    def __init__(self, bot_data: Bot, exchange: ExchangeBase) -> None:
        self.bot_data = bot_data
        self.exchange = exchange
        self.orders = Orders(bot_data=bot_data, exchange=exchange)

    def _price_to_floor(self, price: float) -> int:
        """Convert price to floor"""
        return price_to_floor(
            price=price,
            level_height=self.bot_data.total_level_height,
            level_0_price=self.bot_data.level_0_price,
        )

    def _floor_to_price(self, floor: int) -> float:
        """Convert floor to price"""
        return floor_to_price(
            floor=floor,
            level_height=self.bot_data.total_level_height,
            level_0_price=self.bot_data.level_0_price,
        )

    async def _get_bot(self) -> BotModel:
        """Get bot"""
        async with Session() as session:
            query = select(BotModel).where(BotModel.id == self.bot_data.id)
            bot = (await session.execute(query)).scalar_one_or_none()
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
            level = (await session.execute(query)).scalar_one_or_none()
            if level is not None:
                return level
        level = LevelModel(
            bot_id=self.bot_data.id,
            floor=floor,
            price=self._floor_to_price(floor),
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

    async def place_order_at_level(
        self, floor: int, side: OrderSide, amount: float
    ) -> Order:
        """Place buy order"""
        # TODO: make exeption
        if side == OrderSide.BUY:
            if not await self.can_place_buy_order(floor):
                raise Exception(
                    f"Can't place buy order for this level: {floor}",
                )
        elif side == OrderSide.SELL:
            if not await self.can_place_sell_order(floor):
                raise Exception(
                    f"Can't place sell order for this level: {floor}",
                )

        try:
            order = await self.orders.place_order(
                side=side,
                amount=amount,
                price=self._floor_to_price(floor),
            )
        except Exception as e:
            await self.stop(message=str(e))
            return

        level = await self._get_level(floor)
        async with Session() as session:
            if side == OrderSide.BUY:
                level.set_buy_order(order_id=order.order_id, amount=order.amount)
            elif side == OrderSide.SELL:
                level.set_sell_order(order_id=order.order_id, amount=order.amount)
            session.add(level)
            await session.commit()
        return order

    async def _cancel_opened_buy_order_at_level(self, floor: int) -> LevelModel:
        level = await self._get_level(floor)
        try:
            await self.orders.cancel_order(order_id=level.buy_order_id)
        except Exception as e:
            await self.stop(message=str(e))
            return
        async with Session() as session:
            # update level
            level = await self._get_level(floor)
            level.clear_buy_order()
            session.add(level)
            await session.commit()

    ###########################################################################
    # tick management
    ###########################################################################

    async def _fetch_ticker(self) -> dict:
        """Fetch ticker"""
        ticker = self.exchange.fetch_symbol_ticker(
            symbol=self.bot_data.symbol
        )  # TODO: add error handling
        return ticker

    async def _update_last_price(self) -> dict:
        """Update ticker"""
        self.last_price = (
            self.ticker.get("last")
            or self.ticker.get("close")
            or self.ticker.get("price")
        )
        self.last_floor = self._price_to_floor(self.last_price)
        async with Session() as session:
            query = select(BotModel).where(BotModel.id == self.bot_data.id)
            bot = (await session.execute(query)).scalar_one()
            bot.last_price = self.last_price
            bot.last_floor = self.last_floor
            session.add(bot)
            await session.commit()

    async def tick(self, ticker: dict | None = None) -> None:
        """Handle tick"""
        self.ticker = ticker if ticker else await self._fetch_ticker()
        await self._update_last_price()
        print(f"{self.bot_data.name} >>>>>> tick {self.last_price}")

        await self.orders.update_open_orders()
        await self._process_closed_buy_orders()
        await self._process_closed_sell_orders()

        await self._buy_current_floor_and_down()
        await self._buy_above_current_floor()

        # await self._cancel_excess_buy_orders()

    ###########################################################################
    # trade logic
    ###########################################################################

    async def _process_closed_buy_orders(self) -> None:
        """Process closed buy orders"""
        async with Session() as session:
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot_data.id,
                LevelModel.buy_status == LevelStatus.OPEN,
            )
            result = await session.execute(query)
            levels_to_check = list(result.scalars())
            for level in levels_to_check:
                order = await self.orders.get(level.buy_order_id)
                if order.status == OrderStatus.CLOSED:
                    # place sell order at next level
                    await self.place_order_at_level(
                        level.floor + 1, OrderSide.SELL, level.buy_amount
                    )  # TODO: add maker fee
                    # update level
                    level.clear_buy_order()
                    self.debug(f"level = {level}")
                    session.add(level)
            await session.commit()

    async def _process_closed_sell_orders(self) -> None:
        """Process closed sell orders"""
        async with Session() as session:
            query = select(LevelModel).where(
                LevelModel.bot_id == self.bot_data.id,
                LevelModel.sell_status == LevelStatus.OPEN,
            )
            result = await session.execute(query)
            levels_to_check = list(result.scalars())
            for level in levels_to_check:
                order = await self.orders.get(level.sell_order_id)
                if order.status == OrderStatus.CLOSED:
                    # update level
                    level.clear_sell_order()
                    session.add(level)
            await session.commit()

    async def _buy_current_floor_and_down(self) -> None:
        """If current floor and under are not open buy,
        then we need to place buy orders"""
        for offsset in range(self.bot_data.buy_down_levels):
            target_floor = self.last_floor - offsset
            if await self.can_place_buy_order(target_floor):
                await self.place_order_at_level(
                    floor=target_floor,
                    side=OrderSide.BUY,
                    amount=self.bot_data.trade_amount,
                )

    async def _buy_above_current_floor(self) -> None:
        """If current floor+1 and above are not open buy,
        then we need to place buy orders"""
        for offsset in range(self.bot_data.buy_up_levels):
            target_floor = self.last_floor + offsset + 1
            if await self.can_place_buy_order(target_floor):
                await self.place_order_at_level(
                    floor=target_floor,
                    side=OrderSide.BUY,
                    amount=self.bot_data.trade_amount,
                )

    async def _cancel_excess_buy_orders(self) -> None:
        async with Session() as session:
            query = (
                select(LevelModel.floor)
                .where(
                    LevelModel.bot_id == self.bot_data.id,
                    LevelModel.buy_status == LevelStatus.OPEN,
                    LevelModel.floor < self.last_floor - self.bot_data.buy_down_levels,
                )
                .order_by(LevelModel.floor)
            )
            excess_buy_floors = list((await session.execute(query)).scalars())
        for floor in excess_buy_floors:
            print(f"***** Canceling excess buy order: {floor}")
            await self._cancel_opened_buy_order_at_level(floor)

    ###########################################################################
    # bot control
    ###########################################################################

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
        if message:
            self.debug(message)
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

    def debug(self, message: str, stop: bool = False) -> None:
        """Debug message"""
        from winsound import Beep

        print('-----')
        print(f"{self.bot_data.name} >>>>>> {message}")
        print("\n" * 5)
        Beep(1000, 1000)
        if stop:
            exit()
