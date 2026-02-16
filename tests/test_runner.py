from datetime import datetime, timedelta

from bot.exchange.mexc import OrderStatus
from bot.runner import handle_active_order
from bot.state import ActiveOrder, BotState


class FakePrivateClient:
    def __init__(self, status: OrderStatus):
        self._status = status
        self.canceled_orders: list[tuple[str, str]] = []

    def get_order_status(self, symbol: str, order_id: str) -> OrderStatus:
        return self._status

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        self.canceled_orders.append((symbol, order_id))
        return True


def test_handle_active_order_cancels_partial_fill_when_ttl_expired() -> None:
    state = BotState(
        active_order=ActiveOrder(
            order_id="123",
            side="BUY",
            level="L1",
            price=1.0,
            qty=2.0,
            created_ts=datetime.utcnow() - timedelta(minutes=11),
        )
    )
    private_client = FakePrivateClient(OrderStatus(status="PARTIALLY_FILLED", filled_qty=0.1, orig_qty=2.0))

    handle_active_order(state, mode="LIVE", symbol="XAUTUSDT", private_client=private_client, ttl_minutes=10)

    assert private_client.canceled_orders == [("XAUTUSDT", "123")]
    assert state.active_order is None


def test_handle_active_order_keeps_partial_fill_when_ttl_not_expired() -> None:
    state = BotState(
        active_order=ActiveOrder(
            order_id="123",
            side="BUY",
            level="L1",
            price=1.0,
            qty=2.0,
            created_ts=datetime.utcnow() - timedelta(minutes=2),
        )
    )
    private_client = FakePrivateClient(OrderStatus(status="PARTIALLY_FILLED", filled_qty=0.1, orig_qty=2.0))

    handle_active_order(state, mode="LIVE", symbol="XAUTUSDT", private_client=private_client, ttl_minutes=10)

    assert private_client.canceled_orders == []
    assert state.active_order is not None
    assert state.active_order.status == "PARTIALLY_FILLED"
