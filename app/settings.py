from distutils.debug import DEBUG


DEBUG = True

DEFAULT_LEVEL_HEIGHT = 0.03  # means 3%
DEFAULT_TRADE_AMOUNT = 1.0
DEFAULT_LEVEL_0_PRICE = 1.0
DEFAULT_BUY_UP_LEVELS = 3
DEFAULT_BUY_DOWN_LEVELS = 3


# DATABASE_URL = "sqlite://:memory:"
# DATABASE_URL = f"sqlite:///./database_expobot.db"
DATABASE_URL = f"sqlite+aiosqlite:///database_expobot.db"
# DATABASE_URL = f"sqlite+aiosqlite://"


EXCHANGE_ACCOUNTS = {
    "Backtest Binance": {
        "type": "backtest",
        "description": "Backtest account for testing",
        "exchange": "binance",
    },
    "VirtaBina": {
        "type": "virtual",
        "description": "Backtest account for testing",
        "exchange": "binance",
    },
    "Virtual Kuna": {
        "type": "virtual",
        "description": "Virtual account for testing",
        "exchange": "kuna",
    },
    "Real Kuna": {
        "type": "real",
        "description": "Real account on Kuna for trading",
        "exchange": "kuna",
        "api_key": "",
        "api_secret": "",
    },
}

TICK_PERIOD = 6  # in seconds
