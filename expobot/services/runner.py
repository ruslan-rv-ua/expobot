from sqlmodel import select
from services.calculations import floor_to_price, price_to_floor
from models.level import LevelModel, LevelStatus

from models.bot import Bot, BotModel, BotStatus
from models.order import Order, OrderModel, OrderSide, OrderStatus
from .db import Session
from .exchange.base import ExchangeBase


class BotRunner:
    def __init__(self, bot_data: Bot, exchange: ExchangeBase) -> None:
        self.bot_data = bot_data
        self.exchange = exchange

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
        bot = (
            await self.session.query(BotModel)
            .where(BotModel.id == self.bot_data.id)
            .scalar_one_or_none()
        )
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

    async def place_order(self, floor: int, side: OrderSide, amount: float) -> Order:
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

        level = await self._get_level(floor)

        try:
            exchange_order: dict = self.exchange.place_order(
                symbol=self.bot_data.symbol,
                type="limit",
                side=str(side),
                price=level.price,
                amount=amount,
            )
        except Exception as e:
            self.stop(message=str(e))
            return

        fee_data: dict = exchange_order.get("fee")
        if fee_data is not None:
            fee = dict(
                fee_cost=fee_data.get("cost"),
                fee_currency=fee_data.get("currency"),
                fee_rate=fee_data.get("rate"),
            )
        else:
            fee = dict(fee_cost=0, fee_currency='UNKNOWN', fee_rate=0)

        async with Session() as session:
            order = OrderModel(
                bot_id=self.bot_data.id,
                order_id=exchange_order["id"],
                timestamp=exchange_order.get("timestamp"),
                status=OrderStatus.OPEN,
                side=side,
                symbol=exchange_order["symbol"],
                price=exchange_order.get("price"),
                average=exchange_order.get("average"),
                amount=exchange_order.get("amount"),
                cost=exchange_order.get("cost"),
                **fee,
            )
            session.add(order)
            if side == OrderSide.BUY:
                level.set_buy_order(order_id=order.id, amount=order.amount)
            elif side == OrderSide.SELL:
                level.set_sell_order(order_id=order.id, amount=order.amount)
            session.add(level)
            await session.commit()
            await session.refresh(order)
            return order

    async def cancel_opened_buy_order(self, floor: int) -> LevelModel:
        """Cancel opened buy order"""
        # TODO !!!

    async def _update_open_buy_orders(self) -> None:
        """Sync orders in database with orders in exchange"""
        # TODO !!!

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

        # await self._update_open_buy_orders()
        # await self._update_open_sell_orders()

        # await self._process_closed_buy_orders()
        # await self._process_closed_sell_orders()

        await self._buy_current_floor_and_down()
        await self._buy_current_floor_and_up()

        # await self.cancel_excess_buy_orders()

    async def _buy_current_floor_and_down(self) -> None:
        """If current floor and under are not open buy,
        then we need to place buy orders"""
        for offsset in range(self.bot_data.buy_down_levels):
            target_floor = self.last_floor - offsset
            if await self.can_place_buy_order(target_floor):
                await self.place_order(
                    floor=target_floor,
                    side=OrderSide.BUY,
                    amount=self.bot_data.trade_amount,
                )

    async def _buy_current_floor_and_up(self) -> None:
        """If current floor+1 and above are not open buy,
        then we need to place buy orders"""
        for offsset in range(self.bot_data.buy_up_levels):
            target_floor = self.last_floor + offsset + 1
            if await self.can_place_buy_order(target_floor):
                await self.place_order(
                    floor=target_floor, 
                    side=OrderSide.BUY,
                    amount=self.bot_data.trade_amount
                )

    async def _cancel_excess_buy_orders(self) -> None:
        with Session() as session:
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
                await self.cancel_opened_buy_order(floor)

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
