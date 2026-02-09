from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LevelThresholds:
    buy: dict[str, float] = field(
        default_factory=lambda: {
            "L1": -1.2,
            "L2": -1.6,
            "L3": -2.0,
            "L4": -2.5,
        }
    )
    sell: dict[str, float] = field(
        default_factory=lambda: {
            "S1": -0.8,
            "S2": -0.3,
            "S3": 0.0,
        }
    )
    buy_allocations: dict[str, float] = field(
        default_factory=lambda: {"L1": 0.20, "L2": 0.30, "L3": 0.30, "L4": 0.20}
    )


@dataclass
class Settings:
    mode: Literal["DRY_RUN", "LIVE"] = "DRY_RUN"
    loop_seconds: int = 30
    symbol: str = "XAUTUSDT"
    timezone: str = "Europe/Warsaw"
    state_path: Path = Path("state.json")
    log_path: Path = Path("logs/bot.log")
    mexc_base_url: str = "https://api.mexc.com"
    mexc_api_key: str = ""
    mexc_api_secret: str = ""
    xauusd_api_url: str = ""
    xauusd_api_key: str = ""
    order_ttl_minutes: int = 10
    tick_size: float = 0.01
    step_size: float = 0.001
    min_notional: float = 5.0
    buy_price_ticks_offset: int = 0
    sell_price_ticks_offset: int = 0
    balance_refresh_every: int = 5
    thresholds: LevelThresholds = field(default_factory=LevelThresholds)


def get_settings() -> Settings:
    return Settings(
        mode=os.getenv("MODE", "DRY_RUN"),
        loop_seconds=int(os.getenv("LOOP_SECONDS", "30")),
        symbol=os.getenv("SYMBOL", "XAUTUSDT"),
        timezone=os.getenv("TIMEZONE", "Europe/Warsaw"),
        state_path=Path(os.getenv("STATE_PATH", "state.json")),
        log_path=Path(os.getenv("LOG_PATH", "logs/bot.log")),
        mexc_base_url=os.getenv("MEXC_BASE_URL", "https://api.mexc.com"),
        mexc_api_key=os.getenv("MEXC_API_KEY", ""),
        mexc_api_secret=os.getenv("MEXC_API_SECRET", ""),
        xauusd_api_url=os.getenv("XAUUSD_API_URL", ""),
        xauusd_api_key=os.getenv("XAUUSD_API_KEY", ""),
        order_ttl_minutes=int(os.getenv("ORDER_TTL_MINUTES", "10")),
        tick_size=float(os.getenv("TICK_SIZE", "0.01")),
        step_size=float(os.getenv("STEP_SIZE", "0.001")),
        min_notional=float(os.getenv("MIN_NOTIONAL", "5")),
        buy_price_ticks_offset=int(os.getenv("BUY_PRICE_TICKS_OFFSET", "0")),
        sell_price_ticks_offset=int(os.getenv("SELL_PRICE_TICKS_OFFSET", "0")),
        balance_refresh_every=int(os.getenv("BALANCE_REFRESH_EVERY", "5")),
    )
