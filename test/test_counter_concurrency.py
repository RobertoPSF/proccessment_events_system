import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://localhost:8000/counter/1/increment"

TOTAL_REQUESTS = 100
CONCURRENCY = 20


def send_request(_):
    response = requests.post(URL)
    
    print(response.json())

def main():

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        executor.map(send_request, range(TOTAL_REQUESTS))


if __name__ == "__main__":
    main()