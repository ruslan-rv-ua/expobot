from .base import ExchangeBase
import ccxt


class RealExchange(ExchangeBase):
    is_virtual = False
    is_backtest = False

    def __init__(
        self,
        *,
        exchange: str,
        api_key: str,
        api_secret: str,
    ):
        super().__init__(exchange=exchange)
        self.exchange_instance: ccxt.Exchange = self.exchange_class(
            api_key=api_key, secret=api_secret
        )

    def fetch_orders(self, order_ids: list[str]) -> list[dict]:
        """Get list of orders from the list of orders ids"""
        if self.exchange_instance.has["fetchOrders"]:
            return self.exchange_instance.fetch_orders(order_ids)
        orders = []
        for order_id in order_ids:
            orders.append(self.exchange_instance.fetch_order(order_id))
        return orders

    def place_order(
        self, symbol: str, type: str, side: str, amount: float, price: float
    ) -> str:
        """Place order"""
        return self.exchange_instance.create_order(
            symbol=symbol, type=type, side=side, amount=amount, price=price
        )

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        """Cancel order"""
        return self.exchange_instance.cancel_order(symbol=symbol, order_id=order_id)
