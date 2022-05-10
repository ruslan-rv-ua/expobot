import ccxt
import settings


class Exchange:
    def __init__(
        self,
        *,
        exchange: str,
        api_key: str,
        api_secret: str,
        description: str | None = None,
    ):
        self.exchange = exchange
        self.api_key = api_key or None
        self.api_secret = api_secret or None
        self.description = description
        exchange_class = getattr(ccxt, self.exchange)
        if exchange_class is None:
            raise ValueError(f"Exchange `{self.exchange}` is not supported")
        self.exchange_instance: ccxt.Exchange = (
            exchange_class()
        )  # TODO: add api_key and api_secret

    def is_virtual(self) -> bool:
        return self.api_key is None and self.api_secret is None

    def __str__(self) -> str:
        return f'{"[VIRTUAL] " if self.is_virtual() else ""}{self.exchange}'

    def fetch_symbol_info(self, symbol: str) -> dict:
        self.exchange_instance.load_markets()
        return self.exchange_instance.markets.get(symbol)


exchanges: dict[str, Exchange] = {
    exchange_id: Exchange(**exchange_config)
    for exchange_id, exchange_config in settings.EXCHANGE_ACCOUNTS.items()
}
