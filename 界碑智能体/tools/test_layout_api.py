"""Local smoke test for the Study Debug layout API."""

import http.client
import json
import sys
import threading
from pathlib import Path

from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import LAYOUT_FILE, SiteHandler


httpd = ThreadingHTTPServer(("127.0.0.1", 0), SiteHandler)
thread = threading.Thread(target=httpd.serve_forever, daemon=True)
thread.start()
host, port = httpd.server_address

try:
    connection = http.client.HTTPConnection(host, port, timeout=5)
    connection.request("GET", "/api/layout")
    response = connection.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    assert response.status == 200 and payload["ok"]

    layout = payload["layout"]
    encoded = json.dumps(layout, ensure_ascii=False).encode("utf-8")
    connection.request(
        "POST",
        "/api/layout",
        body=encoded,
        headers={"Content-Type": "application/json", "Content-Length": str(len(encoded))},
    )
    response = connection.getresponse()
    result = json.loads(response.read().decode("utf-8"))
    assert response.status == 200 and result["ok"]
    assert LAYOUT_FILE.exists()
    print("LAYOUT_API_OK")
finally:
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=2)
