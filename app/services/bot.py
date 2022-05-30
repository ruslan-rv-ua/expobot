import datetime
from functools import cache
import logging

from sqlmodel import select

from .level import LevelsRunner

from .. import config
from ..models.bot import Bot, BotModel, BotStatus
from ..models.level import LevelStatus
from .db import get_session
from .exchange.manager import exchanges_manager
from .order import OrdersRunner


@cache
def get_bot_runner(bot_id: int) -> "BotRunner":
    """Get bot runner by bot id"""
    with get_session() as session:
        bot = session.exec(select(BotModel).where(BotModel.id == bot_id)).one()
    return BotRunner(bot)


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

        self.busy = False  # TODO: !!! remove
        self.logger.debug(f"Runner created: {self!r}")

    def __repr__(self) -> str:
        return (
            f"BotRunner(#{self.bot.id} {self.bot.symbol} "
            f"@ {self.bot.exchange_account})"
        )

    ###########################################################################
    # tick
    ###########################################################################

    def _update_ticker(self) -> dict:
        """Update ticker"""
        self.exchange.tick()
        self.ticker = self.exchange.fetch_ticker(
            symbol=self.bot.symbol
        )  # TODO: add error handling

        last_price = (
            self.ticker.get("last")
            or self.ticker.get("close")
            or self.ticker.get("price")
        )
        last_floor = self.levels.price_to_floor(last_price)
        session = get_session()
        self.bot.last_price = last_price
        self.bot.last_floor = last_floor
        session.add(self.bot)
        session.commit()
        session.refresh(self.bot)

    def tick(self) -> None:
        """Handle tick"""
        self.logger.debug(f"\nTick: {self!r}")
        self.busy = True

        self.levels.update()

        self._process_bought_levels()
        self._process_sold_levels()

        self._update_ticker()
        self.logger.debug(
            f"Ticker: [{self.bot.last_floor} {self.bot.last_price}] {self}"
        )

        if self.bot.status == BotStatus.RUNNING:
            self.logger.debug(f"Using trading logic: {self}")
            # trade logic
            self._buy_current_floor_and_down()
            self._buy_above_current_floor()

            self.levels.update()
            self._cancel_excess_buy_orders()

        self.busy = False

    ###########################################################################
    # trade logic
    ###########################################################################

    def _process_bought_levels(self) -> None:
        """Process bought levels"""
        bought_levels_list = self.levels.get_list(buy_status=LevelStatus.CLOSED)
        for bought_level in bought_levels_list:
            self.levels.sell_level(
                bought_level.floor + 1, amount=bought_level.buy_amount
            )
            self.levels.clear_buy_level(bought_level.floor)
        self.logger.debug(f"Bought levels processed: {self!r}")

    def _process_sold_levels(self) -> None:
        """Process sold levels"""
        sold_levels_list = self.levels.get_list(sell_status=LevelStatus.CLOSED)
        for sold_level in sold_levels_list:
            self.levels.clear_sell_level(sold_level.floor)
        self.logger.debug(f"Sold levels processed: {self!r}")

    def _buy_current_floor_and_down(self) -> None:
        """If current floor and under are not open buy,
        then we need to place buy orders"""
        levels_mapping = self.levels.get_mapping()
        for offsset in range(self.bot.buy_down_levels):
            target_floor = self.bot.last_floor - offsset
            target_level = levels_mapping.get(target_floor)
            if target_level and target_level.buy_status != LevelStatus.NONE:
                continue
            level_up = levels_mapping.get(target_floor + 1)
            if level_up and level_up.sell_status == LevelStatus.OPEN:
                continue
            self.levels.buy_level(target_floor, amount=self.bot.trade_amount)

    def _buy_above_current_floor(self) -> None:
        """If current floor+1 and above are not open buy,
        then we need to place buy orders"""
        levels_mapping = self.levels.get_mapping()
        for offsset in range(self.bot.buy_up_levels):
            target_floor = self.bot.last_floor + offsset + 1
            target_level = levels_mapping.get(target_floor)
            if target_level and target_level.buy_status != LevelStatus.NONE:
                continue
            level_up = levels_mapping.get(target_floor + 1)
            if level_up and level_up.sell_status == LevelStatus.OPEN:
                continue
            self.levels.buy_level(target_floor, amount=self.bot.trade_amount)

    def _cancel_excess_buy_orders(self) -> None:
        """Cancel excess buy orders"""
        levels_list = self.levels.get_list(buy_status=LevelStatus.OPEN)
        levels_list = [
            level for level in levels_list if level.floor <= self.bot.last_floor
        ]
        excess_levels = levels_list[: -self.bot.buy_down_levels]
        for level in excess_levels:
            self.levels.cancel_buy_level(level.floor)

    ###########################################################################
    # bot control
    ###########################################################################

    def run(self) -> None:
        """Run bot"""
        session = get_session()
        if self.bot.status == BotStatus.STOPPED:
            self.bot.status = BotStatus.RUNNING
            session.add(self.bot)
            session.commit()
            session.refresh(self.bot)
        else:
            raise Exception(f"Bot {self.bot} already running")
        self.message("Running")
        self.logger.info(f"Bot {self.bot} running")

    def stop(self, message: str | None = None) -> None:
        """Stop bot"""
        if message:
            self.debug(message)
        if self.bot.status == BotStatus.RUNNING:
            session = get_session()
            self.bot.status = BotStatus.STOPPED
            self.bot.message = message
            session.add(self.bot)
            session.commit()
            session.refresh(self.bot)
        else:
            raise Exception(f"Bot {self.bot} already stopped")
        self.message("Stopped")
        self.logger.info(f"Bot {self.bot} stopped")

    def message(self, message: str) -> None:
        """Set message"""
        session = get_session()
        self.bot.message = message
        self.bot.message_datetime = datetime.datetime.now()
        session.add(self.bot)
        session.commit()
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
