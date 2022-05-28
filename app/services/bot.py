import asyncio
import datetime
import logging

from sqlmodel import select

from .level import LevelsRunner

from .. import config
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
    logger: logging.Logger = logging.getLogger("bot_runner")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

    def __init__(self, bot: Bot) -> None:
        self.bot = bot  # TODO: remove self._get_bot()
        self.exchange = exchanges_manager.get(
            exchange_account=self.bot.exchange_account
        )
        orders = OrdersRunner(  # TODO: !!!
            bot_id=self.bot.id, exchange=self.exchange, symbol=self.bot.symbol
        )
        self.levels = LevelsRunner(bot=self.bot, orders=orders)

        self.busy = False
        self.logger.debug(f"Runner created: {self!r}")

    def __repr__(self) -> str:
        return (
            f"BotRunner(#{self.bot.id} {self.bot.symbol} @ {self.bot.exchange_account})"
        )

    async def refresh(self) -> None:
        """Refresh bot data"""
        async with SessionLocal() as session:
            await session.refresh(self.bot)

    ###########################################################################
    # tick management
    ###########################################################################

    async def _fetch_ticker(self) -> dict:
        """Fetch ticker"""
        self.exchange.tick()
        ticker = self.exchange.fetch_ticker(
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

    async def tick(self) -> None:
        """Handle tick"""
        self.logger.debug(f"\nTick: {self!r}")
        self.busy = True

        await self.levels.update()

        await self._process_bought_levels()
        await self._process_sold_levels()

        self.ticker = await self._fetch_ticker()
        await self._update_last_price_and_floor()
        self.logger.debug(
            f"Ticker: [{self.bot.last_floor} {self.bot.last_price}] {self}"
        )

        if self.bot.status == BotStatus.RUNNING:
            self.logger.debug(f"Using trading logic: {self}")
            # trade logic
            await self._buy_current_floor_and_down()
            await self._buy_above_current_floor()

            # await self._cancel_excess_buy_orders()

            await self.levels.update()

        self.busy = False

    ###########################################################################
    # trade logic
    ###########################################################################

    async def _process_bought_levels(self) -> None:
        """Process bought levels"""
        bought_levels_list = await self.levels.get_list(buy_status=LevelStatus.CLOSED)
        for bought_level in bought_levels_list:
            await self.levels.sell_level(
                bought_level.floor + 1, amount=bought_level.amount
            )
            await self.levels.clear_buy_level(bought_level.floor)

        self.logger.debug(f"Bought levels processed: {self!r}")

    async def _process_sold_levels(self) -> None:
        """Process sold levels"""
        sold_levels_list = await self.levels.get_list(sell_status=LevelStatus.CLOSED)
        for sold_level in sold_levels_list:
            await self.levels.clear_sell_level(sold_level.floor)

        self.logger.debug(f"Sold levels processed: {self!r}")
        

    async def _buy_current_floor_and_down(self) -> None:
        """If current floor and under are not open buy,
        then we need to place buy orders"""
        levels_mapping = await self.levels.get_mapping()
        for offsset in range(self.bot.buy_down_levels):
            target_floor = self.bot.last_floor - offsset
            target_level = levels_mapping.get(target_floor)
            if target_level and target_level.buy_status != LevelStatus.NONE:
                continue
            level_up = levels_mapping.get(target_floor + 1)
            if level_up and level_up.sell_status == LevelStatus.OPEN:
                continue
            await self.levels.buy_level(target_floor, amount=self.bot.trade_amount)

    async def _buy_above_current_floor(self) -> None:
        """If current floor+1 and above are not open buy,
        then we need to place buy orders"""
        levels_mapping = await self.levels.get_mapping()
        for offsset in range(self.bot.buy_up_levels):
            target_floor = self.bot.last_floor + offsset + 1
            target_level = levels_mapping.get(target_floor)
            if target_level and target_level.buy_status != LevelStatus.NONE:
                continue
            level_up = levels_mapping.get(target_floor + 1)
            if level_up and level_up.sell_status == LevelStatus.OPEN:
                continue
            await self.levels.buy_level(target_floor, amount=self.bot.trade_amount)

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

    async def run(self) -> None:
        """Run bot"""
        while self.busy:
            await asyncio.sleep(1)
        async with SessionLocal() as session:
            if self.bot.status == BotStatus.STOPPED:
                self.bot.status = BotStatus.RUNNING
                session.add(self.bot)
                await session.commit()
                await session.refresh(self.bot)
            else:
                raise Exception(f"Bot {self.bot} already running")
            await self.message("Running")
            self.logger.info(f"Bot {self.bot} running")

    async def stop(self, message: str = None) -> None:
        """Stop bot"""
        while self.busy:
            await asyncio.sleep(1)
        if message:
            self.debug(message)
        async with SessionLocal() as session:
            if self.bot.status == BotStatus.RUNNING:
                self.bot.status = BotStatus.STOPPED
                self.bot.message = message
                session.add(self.bot)
                await session.commit()
                await session.refresh(self.bot)
            else:
                raise Exception(f"Bot {self.bot} already stopped")
            await self.message("Stopped")
            self.logger.info(f"Bot {self.bot} stopped")

    async def message(self, message: str) -> None:
        """Set message"""
        async with SessionLocal() as session:
            self.bot.message = message
            self.bot.message_datetime = datetime.datetime.now()
            session.add(self.bot)
            await session.commit()
            self.logger.warning(f"\n\n{self.bot} : {message}")

    def debug(self, message: str, stop: bool = False) -> None:
        """Debug message"""

        print("-----")
        print(f"{self.bot} >>>>>> {message}")
        print("\n" * 5)
        from winsound import Beep

        Beep(1000, 300)
        if stop:
            exit()
