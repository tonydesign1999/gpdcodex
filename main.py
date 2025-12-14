"""
Command-line interface for the A-share quant simulator.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from quant_simulator import backtest, data_loader, realtime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A-share quant simulator using AkShare data (CLI only; no GUI)",
    )
    # `required=True` ensures running without a subcommand will show help immediately.
    sub = parser.add_subparsers(dest="command", required=True)

    bt = sub.add_parser("backtest", help="Run minute-level backtest")
    bt.add_argument("symbol", help="Stock code, e.g. 600000")
    bt.add_argument("start", help="Start date YYYYMMDD")
    bt.add_argument("end", help="End date YYYYMMDD")
    bt.add_argument("--period", default="5m", help="Bar period, e.g. 1m or 5m")

    rt = sub.add_parser("realtime", help="Start realtime polling loop")
    rt.add_argument("symbols", nargs="+", help="List of stock codes")
    rt.add_argument("--interval", type=int, default=60, help="Polling interval seconds")

    cache = sub.add_parser("cache", help="Download and cache minute history to parquet")
    cache.add_argument("symbol")
    cache.add_argument("start")
    cache.add_argument("end")
    cache.add_argument("--period", default="5m")
    cache.add_argument("--out", type=Path, default=None, help="Optional output path")

    return parser.parse_args()


def run_backtest_cli(args: argparse.Namespace) -> None:
    print(f"Downloading {args.symbol} data ...")
    df = data_loader.load_minute_history(args.symbol, args.start, args.end, args.period)
    if df.empty:
        print("No data returned. Please check symbol/date range or AkShare connectivity.")
        return
    result = backtest.run_backtest(args.symbol, df)
    print("Backtest complete.")
    print(f"Trades: {len(result.trades)}")
    final_equity = result.equity_curve.iloc[-1] if not result.equity_curve.empty else 0.0
    print(f"Final equity: {final_equity:.2f}")
    out = Path(f"backtest_{args.symbol}_{args.start}_{args.end}.csv")
    pd.DataFrame(result.trades).to_csv(out, index=False)
    print(f"Trades saved to {out}")


def run_realtime_cli(args: argparse.Namespace) -> None:
    engine = realtime.RealtimeEngine(args.symbols, data_loader.load_spot, interval=args.interval)
    engine.run_forever()


def run_cache_cli(args: argparse.Namespace) -> None:
    path = data_loader.cache_minute_history(args.symbol, args.start, args.end, args.period)
    if args.out:
        Path(args.out).write_bytes(Path(path).read_bytes())
        print(f"Cached data copied to {args.out}")
    else:
        print(f"Cached to {path}")


def main() -> None:
    args = parse_args()
    if args.command == "backtest":
        run_backtest_cli(args)
    elif args.command == "realtime":
        run_realtime_cli(args)
    elif args.command == "cache":
        run_cache_cli(args)


if __name__ == "__main__":
    main()
