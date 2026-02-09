from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PriceSnapshot:
    bid: float
    ask: float
    fair: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def deviation_pct(self) -> float:
        return ((self.mid - self.fair) / self.fair) * 100


def compute_deviation_pct(xaut_bid: float, xaut_ask: float, fair: float) -> float:
    mid = (xaut_bid + xaut_ask) / 2
    return ((mid - fair) / fair) * 100


def next_buy_level(deviation_pct: float, thresholds: dict[str, float], filled: dict[str, bool]) -> str | None:
    for level in ("L4", "L3", "L2", "L1"):
        if (not filled[level]) and deviation_pct <= thresholds[level]:
            return level
    return None


def next_sell_step(deviation_pct: float, thresholds: dict[str, float], filled: dict[str, bool]) -> str | None:
    for step in ("S1", "S2", "S3"):
        if (not filled[step]) and deviation_pct >= thresholds[step]:
            return step
    return None


def sell_qty(step: str, xaut_balance: float) -> float:
    if step == "S1":
        return xaut_balance * 0.25
    if step == "S2":
        return xaut_balance * 0.50
    if step == "S3":
        return xaut_balance
    raise ValueError(f"Unknown sell step: {step}")
