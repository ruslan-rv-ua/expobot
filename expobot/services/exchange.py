import ccxt
import settings
from fastapi import HTTPException


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
            raise HTTPException(
                status_code=404, detail=f"Exchange `{self.exchange}` not found"
            ) # TODO: replace hardcoded status code with custom one
        self.exchange_instance: ccxt.Exchange = (
            exchange_class()
        )  # TODO: add api_key and api_secret

    def is_virtual(self) -> bool:
        return self.api_key is None and self.api_secret is None

    def __str__(self) -> str:
        return f'{"[VIRTUAL] " if self.is_virtual() else ""}{self.exchange}'

    def fetch_symbol_info(self, symbol: str) -> dict:
        self.exchange_instance.load_markets()
        symbol_info = self.exchange_instance.markets.get(symbol)
        if symbol_info is None:
            raise HTTPException(f"Symbol `{symbol}` is not supported")


exchanges: dict[str, Exchange] = {
    exchange_id: Exchange(**exchange_config)
    for exchange_id, exchange_config in settings.EXCHANGE_ACCOUNTS.items()
}
