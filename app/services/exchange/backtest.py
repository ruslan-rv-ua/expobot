import uuid

import ccxt
from sqlmodel import select

from ...models.order import OrderModel
from ...services.db import SessionLocal
from .base import ExchangeBase


class BacktestExchange(ExchangeBase):
    is_virtual = True
    is_backtest = True

    def __init__(self, *, exchange: str, description: str | None = None, **kwargs):
        super().__init__(exchange=exchange, description=description)
        self.exchange_instance: ccxt.Exchange = self.exchange_class()

    def set_last_price(self, last_price: float) -> None:
        """Set last price"""
        self.last_price = last_price

    async def fetch_orders(self, order_ids: list[str]) -> list[dict]:
        """Fetch orders"""
        async with SessionLocal() as session:
            query = select(OrderModel).where(OrderModel.order_id.in_(order_ids))
            result = await session.execute(query)
        orders_dicts = [OrderModel.from_orm(order).dict() for order in result.scalars()]
        if not orders_dicts:
            return []
        for order_dict in orders_dicts:
            order_dict["id"] = order_dict["order_id"]

        """Mark orders as closed"""
        for order_dict in orders_dicts:
            if order_dict["status"] != "open":
                continue
            if order_dict["side"] == "buy":
                if order_dict["price"] >= self.last_price:
                    order_dict["status"] = "closed"
                    order_dict["average"] = self.last_price
            else:
                if order_dict["price"] <= self.last_price:
                    order_dict["status"] = "closed"
                    order_dict["average"] = self.last_price
        return orders_dicts

    def place_order(
        self, symbol: str, type: str, side: str, amount: float, price: float
    ) -> str:
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

    def cancel_order(self, order_id: str, symbol: str | None = None) -> dict:
        """Cancel order"""
        # TODO: !!! implement
        return dict(id=order_id, status="canceled")
