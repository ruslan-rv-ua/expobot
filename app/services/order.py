from sqlmodel import Session, select

from app.models.bot import BotModel

from ..db import engine
from ..models.order import OrderModel, OrderSide, OrderStatus
from .exchange.base import ExchangeBase


class OrdersRunner:
    def __init__(
        self,
        bot: BotModel,
        exchange: ExchangeBase,
    ) -> None:
        self.bot = bot
        self.exchange = exchange

    def get(self, order_id: str) -> OrderModel:
        """Get order by id"""
        with Session(engine) as session:

            order = session.exec(
                select(OrderModel).where(
                    OrderModel.bot_id == self.bot.id,
                    OrderModel.order_id == order_id,
                )
            ).one_or_none()
            assert order, f"Order {order_id!r} not found"
        return order

    def get_orders(self) -> list[OrderModel]:
        """Get all orders"""
        with Session(engine) as session:
            orders = session.exec(
                select(OrderModel).where(
                    OrderModel.bot_id == self.bot_id,
                )
            ).all()
        return orders

    def update_open_orders(self) -> None:
        """Sync open orders with exchange"""
        with Session(engine) as session:
            open_orders_ids = session.exec(
                select(OrderModel.order_id).where(
                    OrderModel.bot_id == self.bot.id,
                    OrderModel.status == OrderStatus.OPEN,
                )
            ).all()
            if not open_orders_ids:
                return
            ex_orders = self.exchange.fetch_orders(open_orders_ids)
            for ex_order in ex_orders:
                if ex_order["status"] != "closed":
                    continue
                order = self.get(ex_order["id"])
                order.status = OrderStatus.CLOSED
                order.price = ex_order["price"]
                order.average = ex_order["average"]
                order.cost = ex_order["cost"]
                session.add(order)
            session.commit()

    def place_order(
        self, side: OrderSide, amount: float, price: float
    ) -> OrderModel:
        """Place order"""
        exchange_order: dict = self.exchange.place_order(
            symbol=self.bot.symbol,
            type="limit",
            side=str(side),
            price=price,
            amount=amount,
        )

        with Session(engine) as session:
            order = OrderModel(
                bot_id=self.bot.id,
                order_id=exchange_order["id"],
                timestamp=exchange_order.get("timestamp"),
                status=OrderStatus.OPEN,
                side=side,
                symbol=self.bot.symbol,
                price=exchange_order.get("price"),
                average=exchange_order.get("average"),
                amount=exchange_order.get("amount"),
                cost=exchange_order.get("cost"),
            )
            session.add(order)
            session.commit()
            session.refresh(order)
        return order

    def cancel_order(self, order_id: str) -> OrderModel:
        """Cancel order"""
        order = self.get(order_id)
        assert order.status == OrderStatus.OPEN, f"Order {order!r} is not open oder, can't cancel"
        with Session(engine) as session:
            self.exchange.cancel_order(order_id)
            order.status = OrderStatus.CANCELED
            session.add(order)
            session.commit()
            session.refresh(order)
        return order
