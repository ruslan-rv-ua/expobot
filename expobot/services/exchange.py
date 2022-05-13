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
            )  # TODO: replace hardcoded status code with custom one
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
            raise HTTPException(
                status_code=404, datail=f"Symbol `{symbol}` is not supported"
            )
        return symbol_info

    def fetch_symbol_ticker(self, symbol: str) -> dict:
        ticker = self.exchange_instance.fetch_ticker(symbol)

        if ticker is None:
            pass
            raise HTTPException(
                status_code=404, datail=f"Symbol `{symbol}` is not supported"
            )
        if ticker.get("last") is None:
            ticker["last"] = (
                ticker.get("close")
                or ticker["info"].get("last")
                or ticker["info"].get("close")
            )
        return ticker


class ExchangesManager:
    def __init__(self, exchanges_config: dict):
        self.__exchanges_config = exchanges_config
        self.__exchanges = dict.fromkeys(exchanges_config.keys(), None)

    def __getitem__(self, exchange_account) -> Exchange:
        if exchange_account not in self.__exchanges:
            raise HTTPException(
                status_code=404, detail=f"Exchange {exchange_account} not found"
            )
        if self.__exchanges[exchange_account] is None:
            self.__exchanges[exchange_account] = Exchange(
                **self.__exchanges_config[exchange_account]
            )
        return self.__exchanges[exchange_account]


exchanges_manager: ExchangesManager = ExchangesManager(settings.EXCHANGE_ACCOUNTS)
