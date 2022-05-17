VERSION = "0.0.1"

DEFAULT_LEVEL_PERCENT = 3
DEFAULT_BUY_UP_LEVELS = 3
DEFAULT_BUY_DOWN_LEVELS = 3


# DATABASE_URL = "sqlite://:memory:"
DATABASE_URL = f"sqlite://database_expobot.db"
GENERATE_SCHEMAS = True

TORTOISE_CONFIG = {
  "connections": {
    "default": DATABASE_URL
  },
  "apps": {
    "my_app": {
      "models": [
        "models.bot",
        "models.order",
      ],
      "default_connection": "default"
    }
  },
  "use_tz": "False",
  "timezone": "UTC"
}


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
