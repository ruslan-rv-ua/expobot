import requests
from db_setup import setup_db_for_backtest

# host = "http://192.168.1.10:8000/api/bots/1/tick"
host = "http://127.0.0.1:8000/api/bots/1/tick"


setup_db_for_backtest()

response = requests.get(host)
print('first response:', response)

print_every = 1
index = 0
input('Press Enter to start...')
while True:
    response = requests.get(host)
    if index % print_every == 0:
        print(index, response.status_code)
        resp = input('Press Enter to continue or enter something to stop...')
        if resp:
            break
    index += 1
