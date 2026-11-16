"""Exercise 5 - Call a provisioning REST API with requests.
A tiny fake API runs locally, so no lab is needed."""
import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

class FakeApi(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(201); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"status": "provisioned", "imsi": body["imsi"]}).encode())
    def log_message(self, *a): pass

server = HTTPServer(("127.0.0.1", 8099), FakeApi)
threading.Thread(target=server.serve_forever, daemon=True).start()

r = requests.post("http://127.0.0.1:8099/subscribers", json={"imsi": "001010123456001", "key": "test"}, timeout=5)
print("HTTP status:", r.status_code)
print("Response   :", r.json())
assert r.status_code == 201, "Subscriber was not created"
print("PASS: subscriber provisioned")
server.shutdown()

# TRY: send an empty imsi and make the fake API return 400. Assert the 400.
