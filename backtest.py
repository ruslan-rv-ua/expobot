from winsound import Beep

import requests

from db_setup import (create_bot, delete_all_bots, delete_all_levels,
                      delete_all_orders)


def pause(message: str = None):
    Beep(1000, 300)
    if message:
        print(message)
    response = input("Press Enter to continue or something to exit...")
    return response


def setup_db_for_backtest():
    delete_all_bots()
    delete_all_orders()
    delete_all_levels()
    create_bot(
        exchange_account="Backtest Binance",
        symbol="DOT/USDT",
        level_height=0.1,
    )


# host = "http://192.168.1.10:8000/api/bots/1/tick"
host = "http://127.0.0.1:8000/api/bots/1/tick"


setup_db_for_backtest()

response = requests.get(host)
print("first response:", response)

print_every = 5000
index = 0
input("Press Enter to start...")
while True:
    response = requests.get(host)
    if response.status_code != 200:
        print(index, response, "\a")
        break
    if index % print_every == 0:
        print(index, response)
        resp = pause()
        if resp:
            break
    index += 1
