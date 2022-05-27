import json
import pathlib

file_name = pathlib.Path(__file__).parent.absolute() / "candles_binance_dot_usdt_1h.json"

with open(file_name, "r") as f:
    candles_binance_dot_usdt_1h = json.load(f)


EXCHANGE_ACCOUNTS = {
    "Backtest Binance": {
        "type": "backtest",
        "exchange": "binance",
        "candles": candles_binance_dot_usdt_1h
    },
    "Virtal Binance": {
        "type": "virtual",
        "exchange": "binance",
    },
    "Virtual Kuna": {
        "type": "virtual",
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
