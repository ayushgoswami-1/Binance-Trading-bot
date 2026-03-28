#!/usr/bin/env python3
"""
cli.py – Command-line interface for the Binance Futures Testnet trading bot.

Usage examples:
    # Market BUY
    python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

    # Limit SELL
    python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3200

    # Stop-Market BUY (bonus order type)
    python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 65000

    # Ping the testnet
    python cli.py ping

    # Check account balances
    python cli.py account
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ── Make sure the project root is on sys.path when running as a script ─────────
sys.path.insert(0, str(Path(__file__).parent))

from bot.client import BinanceFuturesClient, BinanceAPIError, BinanceNetworkError
from bot.logging_config import setup_logging, get_logger
from bot.orders import place_order
from bot.validators import (
    ValidationError,
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

# ── Logger (set up after arg parsing so we know the desired log level) ─────────
logger = None  # initialised in main()

_BANNER = r"""
╔══════════════════════════════════════════════════════╗
║       Binance Futures Testnet – Trading Bot          ║
║       USDT-M Perpetuals                              ║
╚══════════════════════════════════════════════════════╝
"""


# ── Argument parser ────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on the Binance Futures USDT-M Testnet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.01 --price 3200
  python cli.py place --symbol BTCUSDT --side BUY --type STOP_MARKET --quantity 0.001 --stop-price 65000
  python cli.py ping
  python cli.py account
        """,
    )

    # Global options
    parser.add_argument(
        "--api-key",
        default=os.environ.get("BINANCE_TESTNET_API_KEY", ""),
        help="Binance Futures Testnet API key (or set BINANCE_TESTNET_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        default=os.environ.get("BINANCE_TESTNET_API_SECRET", ""),
        help="Binance Futures Testnet API secret (or set BINANCE_TESTNET_API_SECRET env var)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: INFO; file always logs DEBUG)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── place ──────────────────────────────────────────────────────────────────
    place_p = subparsers.add_parser("place", help="Place a new futures order")

    place_p.add_argument(
        "--symbol", "-s",
        required=True,
        help="Trading pair symbol, e.g. BTCUSDT",
    )
    place_p.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    place_p.add_argument(
        "--type", "-t",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET", "market", "limit", "stop_market"],
        help="Order type: MARKET, LIMIT, or STOP_MARKET",
    )
    place_p.add_argument(
        "--quantity", "-q",
        required=True,
        help="Order quantity, e.g. 0.001",
    )
    place_p.add_argument(
        "--price", "-p",
        default=None,
        help="Limit price (required for LIMIT orders), e.g. 30000.50",
    )
    place_p.add_argument(
        "--stop-price",
        default=None,
        help="Stop trigger price (required for STOP_MARKET orders), e.g. 65000",
    )
    place_p.add_argument(
        "--reduce-only",
        action="store_true",
        default=False,
        help="Mark order as reduce-only (will only reduce existing position)",
    )

    # ── ping ───────────────────────────────────────────────────────────────────
    subparsers.add_parser("ping", help="Test connectivity to the Binance Futures Testnet")

    # ── account ────────────────────────────────────────────────────────────────
    subparsers.add_parser("account", help="Display account balances and positions")

    return parser


# ── Command handlers ───────────────────────────────────────────────────────────

def cmd_place(args: argparse.Namespace, client: BinanceFuturesClient) -> int:
    """Validate inputs, place an order, return exit code."""
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity   = validate_quantity(args.quantity)
        price      = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValidationError as exc:
        print(f"\n  ⚠️  Validation error: {exc}\n")
        logger.error("Validation error: %s", exc)
        return 1

    result = place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        reduce_only=args.reduce_only,
    )

    return 0 if result["success"] else 1


def cmd_ping(client: BinanceFuturesClient) -> int:
    """Ping the Binance Futures Testnet and print result."""
    print("\n  🔌  Pinging Binance Futures Testnet…")
    ok = client.ping()
    if ok:
        try:
            server_time = client.get_server_time()
            print(f"  ✅  Connected!  Server time: {server_time} ms\n")
        except (BinanceAPIError, BinanceNetworkError) as exc:
            print(f"  ✅  Connected! (Could not fetch server time: {exc})\n")
        return 0
    else:
        print("  ❌  Ping failed. Check your network or the testnet status.\n")
        return 1


def cmd_account(client: BinanceFuturesClient) -> int:
    """Fetch and display account info."""
    print("\n  🔍  Fetching account information…\n")
    try:
        account = client.get_account()
    except BinanceAPIError as exc:
        print(f"  ❌  API error: {exc}\n")
        logger.error("Account fetch error: %s", exc)
        return 1
    except BinanceNetworkError as exc:
        print(f"  ❌  Network error: {exc}\n")
        logger.error("Account fetch network error: %s", exc)
        return 1

    # Show non-zero balances
    assets = [a for a in account.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
    if assets:
        print("  💰  Non-zero balances:")
        for a in assets:
            print(f"      {a['asset']:10s}  wallet={a['walletBalance']:>18}  unrealised PnL={a.get('unrealizedProfit', '0'):>18}")
    else:
        print("  ℹ️   No non-zero balances found (testnet account may need funding).")

    # Show open positions
    positions = [p for p in account.get("positions", []) if float(p.get("positionAmt", 0)) != 0]
    if positions:
        print("\n  📊  Open Positions:")
        for p in positions:
            print(f"      {p['symbol']:12s}  amt={p['positionAmt']:>12}  entry={p.get('entryPrice','N/A'):>12}  uPnL={p.get('unrealizedProfit','N/A'):>12}")
    else:
        print("\n  ℹ️   No open positions.")

    print()
    return 0


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Initialise logging first so all subsequent code is logged
    global logger
    setup_logging(args.log_level)
    logger = get_logger("cli")

    print(_BANNER)
    logger.info("Trading bot started | command=%s", args.command)

    # Validate credentials
    if not args.api_key or not args.api_secret:
        print(
            "  ❌  API credentials are required.\n"
            "      Set --api-key / --api-secret flags, or export:\n"
            "        BINANCE_TESTNET_API_KEY=<key>\n"
            "        BINANCE_TESTNET_API_SECRET=<secret>\n"
        )
        logger.error("Missing API credentials")
        return 1

    # Build the client
    try:
        client = BinanceFuturesClient(api_key=args.api_key, api_secret=args.api_secret)
    except Exception as exc:
        print(f"  ❌  Failed to initialise client: {exc}\n")
        logger.exception("Client initialisation failed")
        return 1

    # Route to the appropriate sub-command
    if args.command == "place":
        exit_code = cmd_place(args, client)
    elif args.command == "ping":
        exit_code = cmd_ping(client)
    elif args.command == "account":
        exit_code = cmd_account(client)
    else:
        parser.print_help()
        exit_code = 1

    logger.info("Trading bot finished | exit_code=%d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
