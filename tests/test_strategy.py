import pytest
from bot.exchange.mexc import floor_to_step, floor_to_tick
from bot.state import BotState
from bot.strategy.dislocation import compute_deviation_pct, next_buy_level, sell_qty
from bot.strategy.risk import update_emergency_mode


def test_deviation_calculation() -> None:
    deviation = compute_deviation_pct(99.0, 101.0, 100.0)
    assert deviation == 0.0


def test_next_buy_level_prefers_deepest() -> None:
    thresholds = {"L1": -1.2, "L2": -1.6, "L3": -2.0, "L4": -2.5}
    filled = {"L1": False, "L2": False, "L3": False, "L4": False}
    assert next_buy_level(-2.6, thresholds, filled) == "L4"


def test_sell_qty_steps() -> None:
    assert sell_qty("S1", 10) == 2.5
    assert sell_qty("S2", 10) == 5.0
    assert sell_qty("S3", 10) == 10


def test_rounding_price_qty() -> None:
    assert floor_to_tick(10.127, 0.01) == pytest.approx(10.12)
    assert floor_to_step(1.239, 0.001) == pytest.approx(1.239)
    assert floor_to_step(1.239, 0.01) == pytest.approx(1.23)


def test_emergency_mode_on_and_off() -> None:
    state = BotState()
    update_emergency_mode(state, deviation_pct=-5.0)
    assert state.emergency_mode.enabled
    update_emergency_mode(state, deviation_pct=-1.0)
    assert state.emergency_mode.enabled is False
