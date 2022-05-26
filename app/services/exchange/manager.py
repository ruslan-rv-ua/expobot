from functools import cache

from ... import settings
from .backtest import BacktestExchange
from .base import ExchangeBase
from .real import RealExchange
from .virtual import VirtualExchange


class ExchangesManager:
    def __init__(self, exchanges_config: dict):
        self.__exchanges_config = exchanges_config

    @cache
    def get(self, exchange_account) -> ExchangeBase:
        """Get an exchange instance by its account name"""
        if exchange_account not in self.__exchanges_config:
            raise Exception(f"Exchange account `{exchange_account}` not found")
        match self.__exchanges_config[exchange_account]["type"]:
            case "real":
                return RealExchange(**self.__exchanges_config[exchange_account])
            case "virtual":
                return VirtualExchange(**self.__exchanges_config[exchange_account])
            case "backtest":
                return BacktestExchange(**self.__exchanges_config[exchange_account])
            case _:
                raise Exception(
                    f"Exchange account `{exchange_account}` has unknown type"
                )

    def clear_all_caches(self) -> None:
        """Clear all caches for all exchanges"""
        # TODO: thsi function is not used
        for exchange_account in self.__exchanges_config:
            exchange = self.get(exchange_account)
            exchange.clear_caches()


# TODO: make this class a singleton and as dependency injection
exchanges_manager: ExchangesManager = ExchangesManager(settings.EXCHANGE_ACCOUNTS)
