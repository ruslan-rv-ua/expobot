from functools import cache

import settings

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
        if (
            self.__exchanges_config[exchange_account]["api_key"]
            and self.__exchanges_config[exchange_account]["secret"]
        ):
            ex_class = RealExchange
        else:
            ex_class = VirtualExchange
        exchange = ex_class(**self.__exchanges_config[exchange_account])
        return exchange

    def clear_all_caches(self) -> None:
        """Clear all caches for all exchanges"""
        for exchange_account in self.__exchanges_config:
            exchange = self.get(exchange_account)
            exchange.clear_caches()


exchanges_manager: ExchangesManager = ExchangesManager(settings.EXCHANGE_ACCOUNTS)
