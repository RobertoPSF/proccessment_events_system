import uuid
import random
import string
from concurrent.futures import ThreadPoolExecutor

import requests

URL = "http://localhost:8000/events"


def random_payload():

    idempotency_key = str(uuid.uuid4())

    return {
        "type": "user_event",
        "payload": {
            "user_id": str(uuid.uuid4()),
            "action": random.choice(["login", "logout", "purchase"]),
            "data": "".join(random.choices(string.ascii_letters, k=10)),
        },
        "idempotency_key": idempotency_key
    }


def send_request(_):

    body = random_payload()

    try:
        r = requests.post(URL, json=body)

        print(r.json())

    except Exception as e:
        print("error:", e)


def main():

    TOTAL_REQUESTS = 1000
    CONCURRENCY = 20

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        executor.map(send_request, range(TOTAL_REQUESTS))


if __name__ == "__main__":
    main()