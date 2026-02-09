import json, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

STOOQ_URL = "https://stooq.com/q/l/?s=xauusd&f=sd2t2ohlcv&h&e=csv"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            r = httpx.get(STOOQ_URL, timeout=8)
            r.raise_for_status()
            lines = r.text.strip().splitlines()
            header = lines[0].split(",")
            row = lines[1].split(",")
            data = dict(zip(header, row))
            price = float(data["Close"])
            ts = f'{data["Date"]}T{data["Time"]}Z'
            payload = {"price": price, "timestamp": ts}
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            body = json.dumps({"price": None, "timestamp": None, "error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
