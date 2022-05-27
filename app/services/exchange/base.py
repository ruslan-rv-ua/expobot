import ccxt


class ExchangeBase:
    def __init__(
        self,
        *,
        exchange: str,
    ):
        self.exchange = exchange

        self.exchange_class = getattr(ccxt, self.exchange)
        if self.exchange_class is None:
            raise Exception(f"Exchange {self.exchange} not found")

        self._last_ticker_cache = {}

    def __str__(self) -> str:
        return f'{"[VIRTUAL] " if self.is_virtual else ""}{self.exchange}'

    def tick(self) -> None:
        self._last_ticker_cache = {}

    def _fetch_ticker(self, symbol: str) -> dict:
        """Fetch ticker from the exchange"""
        ticker = self.exchange_instance.fetch_ticker(symbol)
        return ticker

    def fetch_ticker(self, symbol: str) -> dict:
        if self._last_ticker_cache.get(symbol) is None:
            ticker = self._fetch_ticker(symbol)
            if ticker.get("last") is None:
                ticker["last"] = (
                    ticker.get("close")
                    or ticker["info"].get("last")
                    or ticker["info"].get("close")
                )
            self._last_ticker_cache[symbol] = ticker
        return self._last_ticker_cache[symbol]

    def fetch_market(self, symbol: str) -> dict:
        self.exchange_instance.load_markets()
        market = self.exchange_instance.markets.get(symbol)
        if market is None:
            raise Exception(f"Symbol {symbol} not found")
        return market

    def fetch_orderbook(self, symbol: str) -> dict:
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
