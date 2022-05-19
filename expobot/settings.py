VERSION = "0.0.1"

DEFAULT_LEVEL_HEIGHT = 0.03 # means 3%
DEFAULT_TRADE_AMOUNT = 1.0
DEFAULT_LEVEL_0_PRICE = 1.0
DEFAULT_BUY_UP_LEVELS = 3
DEFAULT_BUY_DOWN_LEVELS = 3


# DATABASE_URL = "sqlite://:memory:"
# DATABASE_URL = f"sqlite:///./database_expobot.db"
DATABASE_URL = f"sqlite+aiosqlite:///database_expobot.db"


EXCHANGE_ACCOUNTS = {
    "binance_main_account": {
        "description": "Binance Main Account",
        "exchange": "binance",
        "api_key": "",
        "api_secret": "",
    },
    "fake_kuna": {
        "description": "Fake Kuna Account",
        "exchange": "kuna",
        "api_key": "",
        "api_secret": "",
    },
}

TICK_PERIOD = 6 # in seconds