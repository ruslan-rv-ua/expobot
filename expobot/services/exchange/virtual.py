from select import select
import uuid
from .base import ExchangeBase
import ccxt
from services.db import Session
from models.order import OrderModel, OrderStatus


class VirtualExchange(ExchangeBase):
    is_virtual = True

    def __init__(self, *, exchange: str, description: str | None = None, **kwargs):
        super().__init__(exchange=exchange, description=description)
        self.exchange_instance: ccxt.Exchange = self.exchange_class()

    async def fetch_orders(self, order_ids: list[str]) -> list[dict]:
        async with Session() as session:
            query = select([OrderModel]).where(OrderModel.id.in_(order_ids))
            orders = list(await session.execute(query).scalars())
        orders_dicts = [order.to_dict() for order in orders]

        """Mark orders as closed"""
        orderbook = self.fetch_symbol_orderbook(orders[0]["symbol"])
        for order_dict in orders_dicts:    
            if order_dict["side"] == "buy":
                if order_dict["price"] >= orderbook["asks"][0][0]:
                    order_dict["status"] = "closed"
                    order_dict["average"] = orderbook["asks"][0][0]
            else:
                if order_dict["price"] <= orderbook["bids"][0][0]:
                    order_dict["status"] = "closed"
                    order_dict["average"] = orderbook["bids"][0][0]
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
