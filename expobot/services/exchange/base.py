from functools import cache
import ccxt
import settings


class ExchangeBase:
    def __init__(
        self,
        *,
        exchange: str,
        description: str | None = None,
        **kwargs
    ):
        self.exchange = exchange
        self.description = description
        self.exchange_class = getattr(ccxt, self.exchange)
        if self.exchange_class is None:
            raise Exception(f"Exchange {self.exchange} not found")

        self.exchange_instance: ccxt.Exchange = None

    def __str__(self) -> str:
        return f'{"[VIRTUAL] " if self.is_virtual else ""}{self.exchange}'

    def clear_caches(self) -> None:
        self.fetch_symbol_info.cache_clear()
        self.fetch_symbol_ticker.cache_clear()
        self.fetch_symbol_orderbook.cache_clear()

    @cache
    def fetch_symbol_info(self, symbol: str) -> dict:
        self.exchange_instance.load_markets()
        symbol_info = self.exchange_instance.markets.get(symbol)
        if symbol_info is None:
            raise Exception(f"Symbol {symbol} not found")
        return symbol_info

    @cache
    def fetch_symbol_ticker(self, symbol: str) -> dict:
        ticker = self.exchange_instance.fetch_ticker(symbol)
        if ticker.get("last") is None:
            ticker["last"] = (
                ticker.get("close")
                or ticker["info"].get("last")
                or ticker["info"].get("close")
            )
        return ticker

    @cache
    def fetch_symbol_orderbook(self, symbol: str) -> dict:
        """Get orderbook for the symbol"""
        orderbook = self.exchange_instance.fetch_order_book(symbol)
        return orderbook

    def fetch_orders(self, order_ids: list[str]) -> list[dict]:
        """Get list of orders from the list of orders ids"""
        raise NotImplementedError


    def place_order(
        self, symbol: str, type: str, side: str, amount: float, price: float
    ) -> str:
        """Place order"""
        raise NotImplementedError

    def cancel_order(self, order_id: str) -> None:
        """Cancel order"""
        raise NotImplementedError