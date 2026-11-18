"""Run from backend with API at 127.0.0.1:8000; requires no API key."""

import json
from urllib.request import Request, urlopen
from uuid import uuid4

body = {
    "workspace_id": str(uuid4()),
    "document_ids": [str(uuid4())],
    "query": "Tổng cầu gồm những thành phần nào?",
}
request = Request(
    "http://127.0.0.1:8000/api/v1/chat/mock/stream",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
with urlopen(request, timeout=15) as response:
    for line in response:
        print(line.decode("utf-8").rstrip())
