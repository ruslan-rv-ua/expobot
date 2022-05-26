from sqlmodel import select

from ..models.bot import Bot
from ..models.order import OrderModel, OrderSide, OrderStatus
from .db import SessionLocal
from .exchange.base import ExchangeBase


class OrdersRunner:
    def __init__(self, bot_id: int, exchange: ExchangeBase, symbol: str) -> None:
        self.bot_id = bot_id
        self.exchange = exchange
        self.symbol = symbol

    async def get(self, order_id: str) -> OrderModel:
        """Get order by id"""
        async with SessionLocal() as session:
            query = select(OrderModel).where(
                OrderModel.bot_id == self.bot_id, OrderModel.order_id == order_id
            )
            order = (await session.execute(query)).scalar_one_or_none()
            if order is None:
                raise Exception(f"Order {order_id} not found")
            return order

    async def get_orders(self) -> list:
        """Get all orders"""
        async with SessionLocal() as session:
            query = select(OrderModel).where(OrderModel.bot_id == self.bot_id)
            orders = await session.execute(query)
            return list(orders.scalars())

    async def update_open_orders(self) -> None:
        """Update status of open orders"""
        self.exchange.clear_caches()
        async with SessionLocal() as session:
            query = select(OrderModel.order_id).where(
                OrderModel.bot_id == self.bot_id,
                OrderModel.status == OrderStatus.OPEN,
            )
            result = await session.execute(query)
            open_orders_ids = list(result.scalars())
        if not open_orders_ids:
            return
        ex_orders = await self.exchange.fetch_orders(open_orders_ids)
        async with SessionLocal() as session:
            for ex_order in ex_orders:
                if ex_order["status"] != "closed":
                    continue
                order = await self.get(ex_order["id"])
                order.status = OrderStatus.CLOSED
                order.average = ex_order["average"]
                order.cost = ex_order["cost"]
                session.add(order)
            await session.commit()

    async def place_order(
        self, side: OrderSide, amount: float, price: float
    ) -> OrderModel:
        """Place order"""
        exchange_order: dict = self.exchange.place_order(
            symbol=self.symbol,
            type="limit",
            side=str(side),
            price=price,
            amount=amount,
        )

        async with SessionLocal() as session:
            order = OrderModel(
                bot_id=self.bot_id,
                order_id=exchange_order["id"],
                timestamp=exchange_order.get("timestamp"),
                status=OrderStatus.OPEN,
                side=side,
                symbol=self.symbol,
                price=exchange_order.get("price"),
                average=exchange_order.get("average"),
                amount=exchange_order.get("amount"),
                cost=exchange_order.get("cost"),
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)
        return order

    async def cancel_order(self, order_id: str) -> OrderModel:
        """Cancel order"""
        async with SessionLocal() as session:
            order = await self.get(order_id)
            if order.status != OrderStatus.OPEN:
                raise Exception(f"Order {order_id} is not open")
            self.exchange.cancel_order(order_id)
            order.status = OrderStatus.CANCELED
            session.add(order)
            await session.commit()
            await session.refresh(order)
        return order
