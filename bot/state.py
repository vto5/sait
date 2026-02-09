from __future__ import annotations

import json
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal


@dataclass
class ActiveOrder:
    order_id: str
    side: Literal["BUY", "SELL"]
    level: str
    price: float
    qty: float
    created_ts: datetime
    status: str = "NEW"
    filled_qty: float = 0.0


@dataclass
class EmergencyState:
    enabled: bool = False
    reason: str = ""


@dataclass
class XauHistoryPoint:
    ts: datetime
    price: float


@dataclass
class BotState:
    balances: dict[str, float] = field(default_factory=lambda: {"XAUT": 0.0, "USDT": 0.0})
    filled_buy_levels: dict[str, bool] = field(
        default_factory=lambda: {"L1": False, "L2": False, "L3": False, "L4": False}
    )
    filled_sell_steps: dict[str, bool] = field(
        default_factory=lambda: {"S1": False, "S2": False, "S3": False}
    )
    active_order: ActiveOrder | None = None
    emergency_mode: EmergencyState = field(default_factory=EmergencyState)
    xauusd_history: list[XauHistoryPoint] = field(default_factory=list)
    events: list[str] = field(default_factory=list)

    def add_event(self, event: str) -> None:
        ring = deque(self.events, maxlen=10)
        ring.append(f"{datetime.utcnow().isoformat()}Z | {event}")
        self.events = list(ring)

    def prune_history(self, now: datetime) -> None:
        cutoff = now - timedelta(hours=24)
        self.xauusd_history = [p for p in self.xauusd_history if p.ts >= cutoff]


def _to_datetime(v: str | datetime) -> datetime:
    if isinstance(v, datetime):
        return v
    return datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)


def _state_from_dict(data: dict) -> BotState:
    active = data.get("active_order")
    active_order = None
    if active:
        active["created_ts"] = _to_datetime(active["created_ts"])
        active_order = ActiveOrder(**active)
    history = [XauHistoryPoint(ts=_to_datetime(p["ts"]), price=float(p["price"])) for p in data.get("xauusd_history", [])]
    em = EmergencyState(**data.get("emergency_mode", {}))
    return BotState(
        balances=data.get("balances", {"XAUT": 0.0, "USDT": 0.0}),
        filled_buy_levels=data.get("filled_buy_levels", {"L1": False, "L2": False, "L3": False, "L4": False}),
        filled_sell_steps=data.get("filled_sell_steps", {"S1": False, "S2": False, "S3": False}),
        active_order=active_order,
        emergency_mode=em,
        xauusd_history=history,
        events=data.get("events", []),
    )


def _state_to_dict(state: BotState) -> dict:
    data = asdict(state)
    if state.active_order:
        data["active_order"]["created_ts"] = state.active_order.created_ts.isoformat()
    data["xauusd_history"] = [{"ts": p.ts.isoformat(), "price": p.price} for p in state.xauusd_history]
    return data


class StateStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> BotState:
        if not self.path.exists():
            return BotState()
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return _state_from_dict(data)

    def save(self, state: BotState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(_state_to_dict(state), f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)
