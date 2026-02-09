from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta

from rich.live import Live

from bot.config import get_settings
from bot.data_providers.xauusd_provider import XauUsdProvider
from bot.exchange.mexc import MexcAuthError, MexcPrivate, MexcPublic, floor_to_step, floor_to_tick
from bot.state import ActiveOrder, BotState, StateStore
from bot.strategy.dislocation import compute_deviation_pct, next_buy_level, next_sell_step, sell_qty
from bot.strategy.risk import update_emergency_mode, update_xau_history
from bot.ui.tui import build_layout


def setup_logging(path: str) -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    from pathlib import Path

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(path)
    fh.setFormatter(fmt)
    logger.addHandler(fh)


def refresh_balances_live(state: BotState, private_client: MexcPrivate) -> None:
    usdt, xaut = private_client.get_balances()
    state.balances["USDT"] = usdt
    state.balances["XAUT"] = xaut


def apply_simulated_fill(state: BotState, side: str, qty: float, price: float, level: str) -> None:
    if side == "BUY":
        state.balances["USDT"] -= qty * price
        state.balances["XAUT"] += qty
        if level.startswith("L"):
            state.filled_buy_levels[level] = True
    else:
        state.balances["XAUT"] -= qty
        state.balances["USDT"] += qty * price
        if level.startswith("S"):
            state.filled_sell_steps[level] = True
    state.add_event(f"SIMULATED {side} {level} filled qty={qty:.6f} price={price:.4f}")


def handle_active_order(
    state: BotState,
    mode: str,
    symbol: str,
    private_client: MexcPrivate | None,
    ttl_minutes: int,
) -> None:
    if state.active_order is None or mode != "LIVE" or private_client is None:
        return

    ao = state.active_order
    status = private_client.get_order_status(symbol, ao.order_id)
    ao.status = status.status
    ao.filled_qty = status.filled_qty

    if status.status == "FILLED":
        if ao.level.startswith("L"):
            state.filled_buy_levels[ao.level] = True
        elif ao.level.startswith("S"):
            state.filled_sell_steps[ao.level] = True
        refresh_balances_live(state, private_client)
        state.add_event(f"Order {ao.order_id} FILLED")
        state.active_order = None
        return

    if status.status == "PARTIALLY_FILLED":
        state.add_event(f"Order {ao.order_id} partially filled {status.filled_qty:.6f}/{status.orig_qty:.6f}")
        return

    if status.status in {"CANCELED", "REJECTED", "EXPIRED"}:
        state.add_event(f"Order {ao.order_id} ended with status={status.status}")
        state.active_order = None
        return

    age_limit = ao.created_ts + timedelta(minutes=ttl_minutes)
    if status.status == "NEW" and datetime.utcnow() > age_limit:
        private_client.cancel_order(symbol, ao.order_id)
        state.add_event(f"Order {ao.order_id} canceled by TTL")
        state.active_order = None


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["DRY_RUN", "LIVE"], default=settings.mode)
    parser.add_argument("--loop-seconds", type=int, default=settings.loop_seconds)
    parser.add_argument("--symbol", default=settings.symbol)
    args = parser.parse_args()

    setup_logging(str(settings.log_path))

    mode = args.mode
    loop_seconds = args.loop_seconds
    symbol = args.symbol

    state_store = StateStore(settings.state_path)
    state = state_store.load()

    public_client = MexcPublic(settings.mexc_base_url)
    private_client = None
    warnings: list[str] = []

    if mode == "LIVE":
        if not settings.mexc_api_key or not settings.mexc_api_secret:
            warnings.append("LIVE disabled: missing MEXC keys, fallback to DRY_RUN")
            mode = "DRY_RUN"
        else:
            private_client = MexcPrivate(
                api_key=settings.mexc_api_key,
                api_secret=settings.mexc_api_secret,
                base_url=settings.mexc_base_url,
            )
            try:
                private_client.auth_test()
                refresh_balances_live(state, private_client)
                try:
                    exch = private_client.get_exchange_info(symbol)
                    if exch.get("tick_size"):
                        settings.tick_size = exch["tick_size"]
                    if exch.get("step_size"):
                        settings.step_size = exch["step_size"]
                    if exch.get("min_notional"):
                        settings.min_notional = exch["min_notional"]
                except Exception:  # noqa: BLE001
                    pass
            except MexcAuthError as exc:
                warnings.append(f"LIVE disabled auth error: {exc}")
                state.add_event(str(exc))
                mode = "DRY_RUN"
                private_client = None

    if state.balances["USDT"] == 0 and mode == "DRY_RUN":
        state.balances["USDT"] = 1000.0

    xau_provider = XauUsdProvider(settings.xauusd_api_url, settings.xauusd_api_key)
    cycles = 0

    with Live(refresh_per_second=2, screen=True) as live:
        while True:
            cycles += 1
            warnings_cycle = warnings.copy()
            bid = ask = fair = deviation = None

            try:
                bid, ask = public_client.get_book_ticker(symbol)
                xau_quote = xau_provider.fetch()
                if xau_quote.price is None:
                    warnings_cycle.append(xau_quote.unavailable_reason or "XAUUSD unavailable")
                    state.add_event(xau_quote.unavailable_reason or "XAUUSD unavailable")
                    state_store.save(state)
                    live.update(
                        build_layout(state, mode, loop_seconds, settings.timezone, None, bid, ask, None, warnings_cycle)
                    )
                    time.sleep(loop_seconds)
                    continue

                fair = xau_quote.price
                now = datetime.utcnow()
                update_xau_history(state, fair, now)
                deviation = compute_deviation_pct(bid, ask, fair)
                update_emergency_mode(state, deviation)

                if mode == "LIVE" and private_client and cycles % settings.balance_refresh_every == 0:
                    refresh_balances_live(state, private_client)

                handle_active_order(state, mode, symbol, private_client, settings.order_ttl_minutes)

                if state.active_order is None and not state.emergency_mode.enabled:
                    buy_level = next_buy_level(deviation, settings.thresholds.buy, state.filled_buy_levels)
                    sell_step = next_sell_step(deviation, settings.thresholds.sell, state.filled_sell_steps)

                    if buy_level:
                        base_price = bid + settings.buy_price_ticks_offset * settings.tick_size
                        limit_price = floor_to_tick(base_price, settings.tick_size)
                        usdt_free = state.balances["USDT"]
                        buy_usdt = usdt_free * settings.thresholds.buy_allocations[buy_level]
                        qty = floor_to_step(buy_usdt / limit_price, settings.step_size)
                        if limit_price * qty < settings.min_notional or qty <= 0:
                            warnings_cycle.append(f"BUY {buy_level} skipped: below min_notional")
                        else:
                            if mode == "DRY_RUN":
                                apply_simulated_fill(state, "BUY", qty, limit_price, buy_level)
                            else:
                                assert private_client is not None
                                oid = private_client.place_limit_order(symbol, "BUY", limit_price, qty)
                                state.active_order = ActiveOrder(
                                    order_id=oid,
                                    side="BUY",
                                    level=buy_level,
                                    price=limit_price,
                                    qty=qty,
                                    created_ts=datetime.utcnow(),
                                )
                                state.add_event(f"BUY {buy_level} placed id={oid} qty={qty:.6f} @ {limit_price:.4f}")

                    elif sell_step and state.balances["XAUT"] > 0:
                        base_price = ask - settings.sell_price_ticks_offset * settings.tick_size
                        limit_price = floor_to_tick(base_price, settings.tick_size)
                        qty = floor_to_step(sell_qty(sell_step, state.balances["XAUT"]), settings.step_size)
                        if limit_price * qty < settings.min_notional or qty <= 0:
                            warnings_cycle.append(f"SELL {sell_step} skipped: below min_notional")
                        else:
                            if mode == "DRY_RUN":
                                apply_simulated_fill(state, "SELL", qty, limit_price, sell_step)
                            else:
                                assert private_client is not None
                                oid = private_client.place_limit_order(symbol, "SELL", limit_price, qty)
                                state.active_order = ActiveOrder(
                                    order_id=oid,
                                    side="SELL",
                                    level=sell_step,
                                    price=limit_price,
                                    qty=qty,
                                    created_ts=datetime.utcnow(),
                                )
                                state.add_event(f"SELL {sell_step} placed id={oid} qty={qty:.6f} @ {limit_price:.4f}")

                elif state.emergency_mode.enabled:
                    warnings_cycle.append(f"EMERGENCY: {state.emergency_mode.reason}")

            except MexcAuthError as exc:
                warnings_cycle.append(f"Trading blocked: {exc}")
                state.add_event(f"MEXC auth error: {exc}")
                mode = "DRY_RUN"
                private_client = None
            except Exception as exc:  # noqa: BLE001
                warnings_cycle.append(str(exc))
                state.add_event(f"Loop error: {exc}")

            state_store.save(state)
            live.update(build_layout(state, mode, loop_seconds, settings.timezone, fair, bid, ask, deviation, warnings_cycle))
            time.sleep(loop_seconds)


if __name__ == "__main__":
    main()
