import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

STOOQ_URL = "https://stooq.com/q/l/?s=xauusd&f=sd2t2ohlcv&h&e=csv"
YAHOO_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=XAUUSD%3DX"


def fetch_from_yahoo(timeout: float = 8.0) -> dict:
    response = httpx.get(YAHOO_URL, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    result = payload.get("quoteResponse", {}).get("result", [])
    if not result:
        raise ValueError("Yahoo response has no quote result")

    quote = result[0]
    price = float(quote["regularMarketPrice"])
    timestamp = quote.get("regularMarketTime")
    if timestamp is None:
        raise ValueError("Yahoo response has no regularMarketTime")

    ts = datetime.datetime.fromtimestamp(int(timestamp), tz=datetime.timezone.utc).isoformat()
    return {"price": price, "timestamp": ts, "source": "yahoo"}


def fetch_from_stooq(timeout: float = 8.0) -> dict:
    response = httpx.get(STOOQ_URL, timeout=timeout)
    response.raise_for_status()

    lines = [line.strip() for line in response.text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Stooq response does not contain data rows")

    header = [item.strip() for item in lines[0].split(",")]
    row = [item.strip() for item in lines[1].split(",")]
    data = dict(zip(header, row))

    close = data.get("Close")
    if close in {None, "", "N/D"}:
        raise ValueError("Stooq response has empty Close field")

    date = data.get("Date")
    if not date:
        raise ValueError("Stooq response has no Date field")
    time = data.get("Time") or "00:00:00"

    price = float(close)
    ts = f"{date}T{time}Z"
    return {"price": price, "timestamp": ts, "source": "stooq"}


def fetch_gold_quote(timeout: float = 8.0) -> dict:
    errors: list[str] = []

    for fetcher in (fetch_from_yahoo, fetch_from_stooq):
        try:
            return fetcher(timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{fetcher.__name__}: {exc}")

    raise RuntimeError("; ".join(errors))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            payload = fetch_gold_quote(timeout=8.0)
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:  # noqa: BLE001
            body = json.dumps({"price": None, "timestamp": None, "error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
