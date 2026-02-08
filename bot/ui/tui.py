from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bot.state import BotState


def _levels_table(title: str, mapping: dict[str, bool]) -> Panel:
    t = Table(expand=True)
    t.add_column("Level")
    t.add_column("State")
    for k, v in mapping.items():
        t.add_row(k, "filled" if v else "waiting")
    return Panel(t, title=title)


def build_layout(
    state: BotState,
    mode: str,
    loop_seconds: int,
    tz_name: str,
    xauusd: float | None,
    bid: float | None,
    ask: float | None,
    deviation: float | None,
    warnings: list[str],
) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="events", size=8),
    )
    layout["body"].split_row(Layout(name="left"), Layout(name="right"))

    now = datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M:%S")
    status = "EMERGENCY" if state.emergency_mode.enabled else "ACTIVE"
    color = "red" if state.emergency_mode.enabled else "green"
    mode_text = f"{mode} SIMULATED" if mode == "DRY_RUN" else "LIVE"
    layout["header"].update(
        Panel(Text(f"Status: {status} | Mode: {mode_text} | Time: {now} | Loop: {loop_seconds}s", style=color))
    )

    p = Table(expand=True)
    p.add_column("Metric")
    p.add_column("Value")
    p.add_row("XAUUSD", "N/A" if xauusd is None else f"{xauusd:.4f}")
    p.add_row("XAUT bid", "N/A" if bid is None else f"{bid:.4f}")
    p.add_row("XAUT ask", "N/A" if ask is None else f"{ask:.4f}")
    mid = None if bid is None or ask is None else (bid + ask) / 2
    p.add_row("XAUT mid", "N/A" if mid is None else f"{mid:.4f}")
    p.add_row("Deviation %", "N/A" if deviation is None else f"{deviation:.4f}%")

    pos = Table(expand=True)
    pos.add_column("Position")
    pos.add_column("Value")
    xaut = state.balances.get("XAUT", 0.0)
    usdt = state.balances.get("USDT", 0.0)
    used = 0.0
    if mid and (xaut * mid + usdt) > 0:
        used = (xaut * mid) / (xaut * mid + usdt) * 100
    pos.add_row("XAUT", f"{xaut:.6f}")
    pos.add_row("USDT free", f"{usdt:.2f}")
    pos.add_row("Used capital", f"{used:.2f}%")

    order = Table(expand=True)
    order.add_column("Field")
    order.add_column("Value")
    if state.active_order:
        ao = state.active_order
        age = (datetime.utcnow() - ao.created_ts.replace(tzinfo=None)).total_seconds() / 60
        order.add_row("id", ao.order_id)
        order.add_row("side", ao.side)
        order.add_row("level", ao.level)
        order.add_row("price", f"{ao.price:.4f}")
        order.add_row("qty", f"{ao.qty:.6f}")
        order.add_row("filled", f"{ao.filled_qty:.6f}")
        order.add_row("status", ao.status)
        order.add_row("age(min)", f"{age:.1f}")
    else:
        order.add_row("active_order", "none")

    left = Layout()
    left.split_column(Layout(Panel(p, title="Prices")), Layout(Panel(pos, title="Position")), Layout(_levels_table("Buy Levels", state.filled_buy_levels)))

    right = Layout()
    right.split_column(
        Layout(_levels_table("Sell Steps", state.filled_sell_steps)),
        Layout(Panel(order, title="Active Order")),
        Layout(Panel("\n".join(warnings + ([state.emergency_mode.reason] if state.emergency_mode.reason else [])) or "None", title="Warnings")),
    )

    layout["left"].update(left)
    layout["right"].update(right)
    layout["events"].update(Panel("\n".join(state.events[-10:]) or "No events", title="Events"))
    return layout
