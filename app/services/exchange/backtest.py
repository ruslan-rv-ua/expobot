import uuid

import ccxt
from sqlmodel import select, Session

from ...db import engine
from ...models.order import OrderModel
from .base import ExchangeBase


class BacktestExchange(ExchangeBase):
    is_virtual = True
    is_backtest = True

    def __init__(self, *, exchange: str, candles: list[dict]):
        super().__init__(exchange=exchange)
        self.exchange_instance: ccxt.Exchange = self.exchange_class()
        self.candles = candles
        self.candle_index = 0

    def _fetch_ticker(self, symbol: str) -> dict:
        ticker = self.candles[self.candle_index]
        self.candle_index += 1
        return ticker

    def fetch_orders(self, order_ids: list[str]) -> list[dict]:
        """Fetch orders"""
        with Session(engine) as session:
            orders = session.exec(
                select(OrderModel).where(OrderModel.order_id.in_(order_ids))
            ).all()
            orders_dicts = [OrderModel.from_orm(order).dict() for order in orders]
        if not orders_dicts:
            return []
        for order_dict in orders_dicts:
            order_dict["id"] = order_dict["order_id"]

        """Mark orders as closed"""
        symbol = orders_dicts[0]["symbol"]
        last_price = self.fetch_ticker(symbol)["last"]
        for order_dict in orders_dicts:
            if order_dict["status"] != "open":
                continue
            if order_dict["side"] == "buy":
                if order_dict["price"] >= last_price:
                    order_dict["status"] = "closed"
                    order_dict["average"] = last_price
            else:
                if order_dict["price"] <= last_price:
                    order_dict["status"] = "closed"
                    order_dict["average"] = last_price
        return orders_dicts

    def place_order(
        self, symbol: str, type: str, side: str, amount: float, price: float
    ) -> dict:
        """Place order"""
        order = dict(
            id=str(uuid.uuid4()),
            symbol=symbol,
            type=type,
            side=side,
            amount=amount,
            price=price,
            status="open",
            average=price,
            cost=amount * price,
        )
        return order

    def cancel_order(self, order_id: str) -> dict:
        """Cancel order"""
        with Session(engine) as session:
            order = session.exec(
                select(OrderModel).where(OrderModel.order_id == order_id)
            ).one()
            order = OrderModel.from_orm(order).dict()
            order["status"] = "canceled"
        return order
