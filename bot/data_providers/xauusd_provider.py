from __future__ import annotations

from dataclasses import dataclass

try:
    import httpx
except Exception:  # noqa: BLE001
    httpx = None


@dataclass
class XauUsdQuote:
    price: float | None
    unavailable_reason: str | None = None


class XauUsdProvider:
    """Expected JSON payload: {"price": float, "timestamp": "ISO-8601"}."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 8.0):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout

    def fetch(self) -> XauUsdQuote:
        if httpx is None:
            return XauUsdQuote(price=None, unavailable_reason="httpx dependency missing")
        if not self.base_url:
            return XauUsdQuote(price=None, unavailable_reason="XAUUSD_API_URL missing")
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(self.base_url, headers=headers)
                r.raise_for_status()
                payload = r.json()
            price = float(payload["price"])
            return XauUsdQuote(price=price)
        except Exception as exc:  # noqa: BLE001
            return XauUsdQuote(price=None, unavailable_reason=f"XAUUSD unavailable: {exc}")
