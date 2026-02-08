from __future__ import annotations

from datetime import datetime

from bot.state import BotState, XauHistoryPoint


def xauusd_24h_change_pct(state: BotState) -> float:
    if len(state.xauusd_history) < 2:
        return 0.0
    first = state.xauusd_history[0].price
    last = state.xauusd_history[-1].price
    if first == 0:
        return 0.0
    return ((last - first) / first) * 100


def update_xau_history(state: BotState, xauusd_price: float, now: datetime) -> None:
    state.xauusd_history.append(XauHistoryPoint(ts=now, price=xauusd_price))
    state.prune_history(now)


def update_emergency_mode(state: BotState, deviation_pct: float) -> None:
    drop_24h = xauusd_24h_change_pct(state)
    enter = deviation_pct <= -4.5 or drop_24h <= -2.0
    exit_ok = deviation_pct > -2.0 and drop_24h > -1.0

    if not state.emergency_mode.enabled and enter:
        reason = []
        if deviation_pct <= -4.5:
            reason.append(f"Deviation {deviation_pct:.2f}% <= -4.5%")
        if drop_24h <= -2.0:
            reason.append(f"XAUUSD 24h {drop_24h:.2f}% <= -2.0%")
        state.emergency_mode.enabled = True
        state.emergency_mode.reason = "; ".join(reason)
        state.add_event(f"EMERGENCY entered: {state.emergency_mode.reason}")
    elif state.emergency_mode.enabled and exit_ok:
        state.emergency_mode.enabled = False
        state.emergency_mode.reason = ""
        state.add_event("EMERGENCY cleared")
