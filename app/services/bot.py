import datetime
import logging

from sqlmodel import select

from .level import LevelsRunner

from .. import settings
from ..models.bot import Bot, BotModel, BotStatus
from ..models.level import LevelModel, LevelStatus
from ..models.order import Order, OrderSide, OrderStatus
from .db import SessionLocal
from .exchange.manager import exchanges_manager
from .order import OrdersRunner

__bot_runners_cache = {}


async def get_bot_runner(bot_id: int) -> "BotRunner":
    """Get bot runner by bot id"""
    global __bot_runners_cache
    async with SessionLocal() as session:
        if bot_id not in __bot_runners_cache:
            bot = (
                await session.execute(select(BotModel).where(BotModel.id == bot_id))
            ).scalar_one_or_none()
            if bot is None:
                raise ValueError(f"Bot with id {bot_id} not found")
            __bot_runners_cache[bot_id] = BotRunner(bot=bot)
        return __bot_runners_cache[bot_id]


class BotRunner:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot  # TODO: remove self._get_bot()
        self.exchange = exchanges_manager.get(
            exchange_account=self.bot.exchange_account
        )
        orders = OrdersRunner(  # TODO: !!!
            bot_id=self.bot.id, exchange=self.exchange, symbol=self.bot.symbol
        )
        self.levels = LevelsRunner(bot=self.bot, orders=orders)

        self.logger = self._create_logger()
        self.logger.debug(f"Runner created: {self}")

    def __repr__(self) -> str:
        return (
            f"BotRunner(#{self.bot.id} {self.bot.symbol} @ {self.bot.exchange_account})"
        )

    def _create_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        return logger

    async def refresh(self) -> None:
        """Refresh bot data"""
        async with SessionLocal() as session:
            await session.refresh(self.bot)

    ###########################################################################
    # tick management
    ###########################################################################

    async def _fetch_ticker(self) -> dict:
        """Fetch ticker"""
        ticker = self.exchange.fetch_symbol_ticker(
            symbol=self.bot.symbol
        )  # TODO: add error handling
        return ticker

    async def _update_last_price_and_floor(self) -> dict:
        """Update ticker"""
        last_price = (
            self.ticker.get("last")
            or self.ticker.get("close")
            or self.ticker.get("price")
        )
        last_floor = self.levels.price_to_floor(last_price)
        async with SessionLocal() as session:
            self.bot.last_price = last_price
            self.bot.last_floor = last_floor
            session.add(self.bot)
            await session.commit()
            await session.refresh(self.bot)

    async def tick(self, last_price: float | None = None) -> None:
        """Handle tick"""
        self.logger.debug(f"Tick: {self!r}")
        await self.levels.update()
        self.logger.debug(f"Levels updated: {self}")

        await self._process_closed_buy_levels()
        self.logger.debug(f"Closed buy levels processed: {self}")

        # self._process_closed_sell_levels()
        # self.logger.debug(f"Closed sell levels processed: {self}")

        is_backtest = last_price is not None
        if is_backtest:
            self.ticker = {"last": last_price}
            self.exchange.set_last_price(last_price)
        else:
            self.ticker = await self._fetch_ticker()
        await self._update_last_price_and_floor()
        self.logger.debug(
            f"Ticker: [{self.bot.last_floor} {self.bot.last_price}] {self}"
        )

        # if self.bot.status == BotStatus.RUNNING:
        if True: # TODO: !!! remove
            # trade logic
            await self._buy_current_floor_and_down()
            await self._buy_above_current_floor()

        # await self._cancel_excess_buy_orders()

    ###########################################################################
    # trade logic
    ###########################################################################

    async def _process_closed_buy_levels(self) -> None:
        """Process closed buy levels"""
        query = select(LevelModel).where(
            LevelModel.bot_id == self.bot.id,
            LevelModel.buy_status == LevelStatus.CLOSED,
        )
        async with SessionLocal() as session:
            result = await session.execute(query)
            levels = result.scalars()
            for level in levels:
                await self.levels.place_order(
                    floor=level.floor + 1, side=OrderSide.SELL, amount=self.bot.trade_amount
                )
                level.clear_buy_order()
                session.add(level)
            await session.commit()

    async def _process_closed_sell_levels(self) -> None:
        """Process closed sell levels"""
        query = select(LevelModel).where(
            LevelModel.bot_id == self.bot.id,
            LevelModel.sell_status == LevelStatus.CLOSED,
        )
        async with SessionLocal() as session:
            levels = await session.execute(query)
            for level in levels:
                level.clear_sell_status()
                session.add(level)
            await session.commit()


    async def _buy_current_floor_and_down(self) -> None:
        """If current floor and under are not open buy,
        then we need to place buy orders"""
        for offsset in range(self.bot.buy_down_levels):
            target_floor = self.bot.last_floor - offsset
            if await self.levels.can_place_buy_order(target_floor):
                await self.levels.place_order(
                    floor=target_floor,
                    side=OrderSide.BUY,
                    amount=self.bot.trade_amount,
                )

    async def _buy_above_current_floor(self) -> None:
        """If current floor+1 and above are not open buy,
        then we need to place buy orders"""
        for offsset in range(self.bot.buy_up_levels):
            target_floor = self.bot.last_floor + offsset + 1
            if await self.levels.can_place_buy_order(target_floor):
                await self.levels.place_order(
                    floor=target_floor,
                    side=OrderSide.BUY,
                    amount=self.bot.trade_amount,
                )

    async def _cancel_excess_buy_orders(self) -> None:
        async with SessionLocal() as session:
            query = (
                select(LevelModel.floor)
                .where(
                    LevelModel.bot_id == self.bot.id,
                    LevelModel.buy_status == LevelStatus.OPEN,
                    LevelModel.floor < self.last_floor - self.bot.buy_down_levels,
                )
                .order_by(LevelModel.floor)
            )
            excess_buy_floors = list((await session.execute(query)).scalars())
        for floor in excess_buy_floors:
            await self._cancel_opened_buy_order_at_level(floor)

    ###########################################################################
    # bot control
    ###########################################################################

    async def start(self) -> Bot:
        """Start bot"""
        async with SessionLocal() as session:
            bot = await self._get_bot()
            if bot.status == BotStatus.STOPPED:
                bot.status = BotStatus.RUNNING
                session.add(bot)
                await session.commit()
                await session.refresh(bot)
            else:
                raise Exception(f"Bot {bot.id} already running")
            self.message("Started")
            return bot

    async def stop(self, message: str = None) -> Bot:
        """Stop bot"""
        if message:
            self.debug(message)
        async with SessionLocal() as session:
            bot = await self._get_bot()
            if bot.status == BotStatus.RUNNING:
                bot.status = BotStatus.STOPPED
                bot.message = message
                session.add(bot)
                await session.commit()
                await session.refresh(bot)
            else:
                raise Exception(f"Bot {bot.id} already stopped")
            self.message("Stopped")
            return bot

    async def message(self, message: str) -> None:
        """Set message"""
        async with SessionLocal() as session:
            bot = await self._get_bot()
            bot.message = message
            bot.message_datetime = datetime.now()
            session.add(bot)
            await session.commit()
            self.logger.warning(f"{self.bot} : {message}")

    def debug(self, message: str, stop: bool = False) -> None:
        """Debug message"""

        print("-----")
        print(f"{self.bot.name} >>>>>> {message}")
        print("\n" * 5)
        from winsound import Beep

        Beep(1000, 300)
        if stop:
            exit()
