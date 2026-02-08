from __future__ import annotations

import hashlib
import hmac
import math
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

try:
    import httpx
except Exception:  # noqa: BLE001
    httpx = None


class MexcAuthError(RuntimeError):
    """Authentication failed, trading must stop."""


@dataclass
class OrderStatus:
    status: str
    filled_qty: float
    orig_qty: float


def floor_to_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return math.floor(value / step) * step


def floor_to_tick(value: float, tick: float) -> float:
    if tick <= 0:
        return value
    return math.floor(value / tick) * tick


def _ensure_httpx() -> None:
    if httpx is None:
        raise RuntimeError("httpx is required for exchange calls")


class MexcPublic:
    def __init__(self, base_url: str = "https://api.mexc.com", timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout

    def get_book_ticker(self, symbol: str) -> tuple[float, float]:
        _ensure_httpx()
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            r = client.get("/api/v3/ticker/bookTicker", params={"symbol": symbol})
            r.raise_for_status()
            p = r.json()
        return float(p["bidPrice"]), float(p["askPrice"])


class MexcPrivate:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.mexc.com",
        timeout: float = 10.0,
        recv_window: int = 5000,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.timeout = timeout
        self.recv_window = recv_window
        self.max_retries = max_retries

    def _signed_request(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        _ensure_httpx()
        params = params.copy() if params else {}
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = self.recv_window
        query = urlencode(params)
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

        headers = {"X-MEXC-APIKEY": self.api_key}
        url = f"{path}?{query}&signature={signature}"

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                    response = client.request(method, url, headers=headers)
                if response.status_code in (401, 403):
                    raise MexcAuthError(f"MEXC auth failed on {path}, status={response.status_code}")
                if response.status_code == 429 and attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as exc:  # noqa: BLE001
                if isinstance(exc, MexcAuthError):
                    raise
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status in (401, 403):
                    raise MexcAuthError(f"MEXC auth/signature error on {path}") from exc
                if attempt >= self.max_retries:
                    raise
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"MEXC request failed after retries: method={method}, path={path}")

    def auth_test(self) -> bool:
        self._signed_request("GET", "/api/v3/account")
        return True

    def get_account_info(self) -> dict[str, Any]:
        return self._signed_request("GET", "/api/v3/account")

    def get_balances(self) -> tuple[float, float]:
        acc = self.get_account_info()
        usdt = 0.0
        xaut = 0.0
        for b in acc.get("balances", []):
            asset = b.get("asset")
            free = float(b.get("free", 0.0))
            if asset == "USDT":
                usdt = free
            elif asset == "XAUT":
                xaut = free
        return usdt, xaut

    def place_limit_order(self, symbol: str, side: str, price: float, quantity: float) -> str:
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": f"{quantity:.12f}".rstrip("0").rstrip("."),
            "price": f"{price:.12f}".rstrip("0").rstrip("."),
            "newOrderRespType": "RESULT",
        }
        data = self._signed_request("POST", "/api/v3/order", payload)
        return str(data.get("orderId"))

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        payload = {"symbol": symbol, "orderId": order_id}
        self._signed_request("DELETE", "/api/v3/order", payload)
        return True

    def get_order_status(self, symbol: str, order_id: str) -> OrderStatus:
        payload = {"symbol": symbol, "orderId": order_id}
        data = self._signed_request("GET", "/api/v3/order", payload)
        return OrderStatus(
            status=str(data.get("status", "UNKNOWN")),
            filled_qty=float(data.get("executedQty", 0.0)),
            orig_qty=float(data.get("origQty", 0.0)),
        )

    def get_exchange_info(self, symbol: str) -> dict[str, float]:
        _ensure_httpx()
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            r = client.get("/api/v3/exchangeInfo", params={"symbol": symbol})
            r.raise_for_status()
            payload = r.json()
        info = {"tick_size": 0.0, "step_size": 0.0, "min_notional": 0.0}
        symbols = payload.get("symbols", [])
        if not symbols:
            return info
        filters = {f.get("filterType"): f for f in symbols[0].get("filters", [])}
        if "PRICE_FILTER" in filters:
            info["tick_size"] = float(filters["PRICE_FILTER"].get("tickSize", 0.0))
        if "LOT_SIZE" in filters:
            info["step_size"] = float(filters["LOT_SIZE"].get("stepSize", 0.0))
        if "MIN_NOTIONAL" in filters:
            info["min_notional"] = float(filters["MIN_NOTIONAL"].get("minNotional", 0.0))
        return info
