# Binance Futures Testnet – Trading Bot

A clean, structured Python CLI application for placing orders on the
**Binance USDT-M Futures Testnet**.

---

## Features

| Feature | Details |
|---|---|
| Order types | `MARKET`, `LIMIT`, `STOP_MARKET` (bonus) |
| Sides | `BUY` and `SELL` |
| CLI | `argparse`-based with clear help text |
| Logging | Rotating file log (`logs/trading_bot.log`) + console output |
| Error handling | Typed exceptions for API errors, network failures, and bad input |
| Structure | Separate `client`, `orders`, and `validators` layers |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package surface
│   ├── client.py            # Binance REST client (signing, requests, errors)
│   ├── orders.py            # Order placement + console formatting
│   ├── validators.py        # Input validation (symbol, side, qty, price…)
│   └── logging_config.py    # Rotating file + console log setup
├── cli.py                   # CLI entry point (argparse)
├── logs/
│   └── trading_bot.log      # Auto-created on first run
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone / unzip

```bash
git clone https://github.com/<your-username>/trading-bot.git
cd trading_bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet credentials

1. Visit <https://testnet.binancefuture.com>
2. Log in with your Binance account (or create a dedicated testnet account)
3. Go to **API Key** → **Generate API Key**
4. Copy your **API Key** and **API Secret**

> ⚠️  The Testnet occasionally resets balances.
> If your account shows no USDT, click **"Generate"** next to the USDT balance
> to claim testnet funds.

### 5. Set credentials

**Option A – environment variables (recommended)**

```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

**Option B – CLI flags**

```bash
python cli.py --api-key "..." --api-secret "..." place ...
```

---

## Usage

All commands accept `--api-key` / `--api-secret` flags **or** read from the
environment variables above.

### Test connectivity

```bash
python cli.py ping
```

### View account balances & positions

```bash
python cli.py account
```

### Place a MARKET order

```bash
# Buy 0.001 BTC at market price
python cli.py place \
  --symbol BTCUSDT \
  --side   BUY \
  --type   MARKET \
  --quantity 0.001
```

### Place a LIMIT order

```bash
# Sell 0.01 ETH at 3 200 USDT (resting order)
python cli.py place \
  --symbol   ETHUSDT \
  --side     SELL \
  --type     LIMIT \
  --quantity 0.01 \
  --price    3200
```

### Place a STOP_MARKET order (bonus)

```bash
# Buy 0.001 BTC when price rises to 65 000 USDT
python cli.py place \
  --symbol     BTCUSDT \
  --side       BUY \
  --type       STOP_MARKET \
  --quantity   0.001 \
  --stop-price 65000
```

### Optional flags

| Flag | Default | Description |
|---|---|---|
| `--reduce-only` | `false` | Only reduce an existing position |
| `--log-level` | `INFO` | Console verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Sample output

### MARKET order

```
╔══════════════════════════════════════════════════════╗
║       Binance Futures Testnet – Trading Bot          ║
║       USDT-M Perpetuals                              ║
╚══════════════════════════════════════════════════════╝

────────────────────────────────────────────────────────
  📋  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Symbol      : BTCUSDT
  Side        : BUY
  Type        : MARKET
  Quantity    : 0.001
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
  ✅  ORDER RESPONSE
────────────────────────────────────────────────────────
  Order ID     : 4611686018530199568
  Symbol       : BTCUSDT
  Side         : BUY
  Type         : MARKET
  Status       : FILLED
  Orig Qty     : 0.001
  Executed Qty : 0.001
  Avg Price    : 84312.10
  Price        : 0
  Update Time  : 1743153311038
────────────────────────────────────────────────────────

  🎉  Order submitted successfully!  Order ID: 4611686018530199568
```

---

## Logging

All activity is written to `logs/trading_bot.log`.

- **File**: always logs at `DEBUG` level (full request/response detail)
- **Console**: logs at the level set by `--log-level` (default `INFO`)
- The file rotates at **5 MB**, keeping the last 5 backups

Log format:
```
YYYY-MM-DD HH:MM:SS | LEVEL    | module               | message
```

Example entries:
```
2025-03-28 10:15:10 | INFO     | bot.client           | Placing order: symbol=BTCUSDT side=BUY type=MARKET qty=0.001
2025-03-28 10:15:11 | INFO     | bot.client           | Order placed successfully: orderId=4611686018530199568 status=FILLED
2025-03-28 10:17:44 | WARNING  | bot.validators       | Validation failed – price: Price is required for LIMIT orders.
```

---

## Error handling

| Error class | Raised when |
|---|---|
| `ValidationError` | Symbol / side / qty / price fails input checks |
| `BinanceAPIError` | Binance returns HTTP 4xx/5xx or `{"code": -XXXX}` |
| `BinanceNetworkError` | Timeout, DNS failure, or connection refused |

All errors are caught in `cli.py`, logged, and printed with a clear
`❌ ORDER FAILED` block before exiting with code `1`.

---

## Assumptions

1. Only **USDT-M perpetual futures** are supported (base URL: `https://testnet.binancefuture.com`).
2. `timeInForce` defaults to `GTC` for LIMIT orders; this can be extended in `client.py`.
3. No position-mode check is performed; the account must be in **One-way mode**
   (Binance Futures default) for `positionSide=BOTH` to work.
4. The `requests` library is the only runtime dependency — no Binance SDK is used,
   keeping the dependency surface minimal.

---

## Running tests (optional)

```bash
pip install pytest pytest-mock
pytest tests/ -v
```

---

## License

MIT
