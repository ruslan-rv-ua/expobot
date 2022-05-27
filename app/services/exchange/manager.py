from functools import cache

from ... import settings
from .backtest import BacktestExchange
from .base import ExchangeBase
from .real import RealExchange
from .virtual import VirtualExchange


class ExchangesManager:
    def __init__(self, exchanges_config: dict):
        self.__exchanges_configs = exchanges_config

    @cache
    def get(self, exchange_account) -> ExchangeBase:
        """Get an exchange instance by its account name"""
        if exchange_account not in self.__exchanges_configs:
            raise Exception(f"Exchange account `{exchange_account}` not found")
        exchange_config = self.__exchanges_configs[exchange_account]
        match exchange_config["type"]:
            case "real":
                return RealExchange(
                    exchange=exchange_config["exchange"],
                    api_key=exchange_config["api_key"],
                    api_secret=exchange_config["api_secret"],
                )
            case "virtual":
                return VirtualExchange(exchange=exchange_config["exchange"])
            case "backtest":
                return BacktestExchange(
                    exchange=exchange_config["exchange"],
                    candles=exchange_config["candles"],
                )
            case _:
                raise Exception(
                    f"Exchange account `{exchange_account}` has unknown type"
                )


# TODO: make this class a singleton and as dependency injection
exchanges_manager: ExchangesManager = ExchangesManager(settings.EXCHANGE_ACCOUNTS)
