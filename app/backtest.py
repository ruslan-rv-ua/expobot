import requests

# host = "http://192.168.1.10:8000/api/bots/1/tick"
host = "http://127.0.0.1:8000/api/bots/1/tick"

print_every = 1
index = 0
while True:
    response = requests.get(host)
    if index % print_every == 0:
        print(index, response.status_code)
    index += 1
