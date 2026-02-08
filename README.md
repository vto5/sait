# MEXC Spot XAUT/USDT Mean-Reversion Bot (MVP)

Production-oriented MVP for **SPOT only** trading on MEXC with strategy **Fair Value Dislocation Mean Reversion** and terminal UI on `rich`.

## Disclaimer

**Не финансовый совет.** Use at your own risk.

## Features

- `DRY_RUN` first (default), `LIVE` only with valid keys.
- Fair value from external `XAUUSD` provider.
- Public MEXC orderbook + signed private MEXC trading endpoints.
- Emergency hold-only mode.
- Local persistent `state.json`.
- Rich full-screen TUI.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

Start with simulation:

```bash
python -m bot.runner --mode DRY_RUN --loop-seconds 30 --symbol XAUTUSDT
```

Live (only after dry validation):

```bash
python -m bot.runner --mode LIVE --loop-seconds 30 --symbol XAUTUSDT
```

If auth check fails in LIVE, bot auto-falls back to DRY_RUN with warning.

## LIVE mode safety

- **Withdraw permission must be OFF** for the API key.
- Start with **DRY_RUN for 1-2 weeks**.
- Then start with **small capital first**.
- Secrets must be provided only through env vars:
  - `MEXC_API_KEY`
  - `MEXC_API_SECRET`
- Never log raw signed headers/signature/query.

## XAUUSD provider format

Expected JSON from `XAUUSD_API_URL`:

```json
{
  "price": 2360.25,
  "timestamp": "2026-01-20T10:22:00Z"
}
```

On provider failure trading is blocked (warning shown in TUI).

## MEXC endpoints used

In `bot/exchange/mexc.py`:

- Public:
  - `GET /api/v3/ticker/bookTicker`
- Signed/private:
  - `GET /api/v3/account` (auth test + balances)
  - `POST /api/v3/order` (limit order)
  - `DELETE /api/v3/order` (cancel)
  - `GET /api/v3/order` (order status)
- Public metadata:
  - `GET /api/v3/exchangeInfo` (tick/step/minNotional)

If your account/region uses different MEXC routes/fields, change these methods in `bot/exchange/mexc.py`.

## Project structure

```text
bot/
  config.py
  state.py
  runner.py
  data_providers/xauusd_provider.py
  exchange/mexc.py
  strategy/dislocation.py
  strategy/risk.py
  ui/tui.py
tests/test_strategy.py
```
