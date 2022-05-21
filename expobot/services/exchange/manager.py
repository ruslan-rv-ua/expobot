from .real import RealExchange
from .virtual import VirtualExchange
from .base import ExchangeBase
import settings


class ExchangesManager:
    def __init__(self, exchanges_config: dict):
        self.__exchanges_config = exchanges_config
        self.__exchanges = dict.fromkeys(exchanges_config.keys(), None)

    def __getitem__(self, exchange_account) -> ExchangeBase:
        """Get an exchange instance by its account name"""
        if exchange_account not in self.__exchanges:
            raise Exception(f"Exchange account `{exchange_account}` not found")
        if self.__exchanges[exchange_account] is None:
            if (
                self.__exchanges_config[exchange_account]["api_key"]
                and self.__exchanges_config[exchange_account]["secret"]
            ):
                ex_class = RealExchange
            else:
                ex_class = VirtualExchange
            self.__exchanges[exchange_account] = ex_class(
                **self.__exchanges_config[exchange_account]
            )
        return self.__exchanges[exchange_account]

    def clear_all_caches(self) -> None:
        """Clear all caches for all exchanges"""
        for exchange in self.__exchanges.values():
            if exchange is not None:
                exchange.clear_caches()


exchanges_manager: ExchangesManager = ExchangesManager(settings.EXCHANGE_ACCOUNTS)
