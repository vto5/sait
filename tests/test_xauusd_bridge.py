import xauusd_bridge


def test_fetch_from_yahoo_parses_price_and_timestamp(monkeypatch):
    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "quoteResponse": {
                    "result": [
                        {
                            "regularMarketPrice": 2361.7,
                            "regularMarketTime": 1737368520,
                        }
                    ]
                }
            }

    monkeypatch.setattr(xauusd_bridge.httpx, "get", lambda *args, **kwargs: DummyResponse())

    quote = xauusd_bridge.fetch_from_yahoo()

    assert quote["price"] == 2361.7
    assert quote["timestamp"].endswith("+00:00")
    assert quote["source"] == "yahoo"


def test_fetch_gold_quote_falls_back_to_stooq(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("yahoo down")

    monkeypatch.setattr(xauusd_bridge, "fetch_from_yahoo", boom)
    monkeypatch.setattr(
        xauusd_bridge,
        "fetch_from_stooq",
        lambda timeout=8.0: {
            "price": 2359.2,
            "timestamp": "2026-01-20T10:22:00Z",
            "source": "stooq",
        },
    )

    quote = xauusd_bridge.fetch_gold_quote()

    assert quote["price"] == 2359.2
    assert quote["source"] == "stooq"
