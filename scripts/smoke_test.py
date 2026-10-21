"""Exercise public catalogue, Authorize JWT header and stock lifecycle over HTTP."""
import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8030/api"


def request(path, data=None, token=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorize"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    with urlopen(Request(BASE + path, data=data, headers=headers), timeout=5) as response:
        return json.load(response)


for attempt in range(30):
    try:
        catalogue = request("/books/")
        break
    except (URLError, TimeoutError, ConnectionError):
        time.sleep(1)
else:
    raise RuntimeError("Library API did not start")

token = request("/users/token/", {"email": "reader@example.com", "password": "Library-demo-2026!"})["access"]
book = next(book for book in catalogue["results"] if book["inventory"] > 0)
from datetime import date, timedelta

borrowing = request("/borrowings/", {"book": book["id"], "expected_return_date": str(date.today() + timedelta(days=2))}, token)
assert request(f"/books/{book['id']}/")["inventory"] == book["inventory"] - 1
returned = request(f"/borrowings/{borrowing['id']}/return/", {}, token)
assert returned["actual_return_date"] is not None
assert request(f"/books/{book['id']}/")["inventory"] == book["inventory"]
assert request("/borrowings/?is_active=false", token=token)["count"] == 1
print("Public catalogue, JWT login, borrowing, return and inventory HTTP checks passed.")
