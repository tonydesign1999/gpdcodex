"""
Realtime polling loop for spot data and strategy execution.
"""
from __future__ import annotations

import datetime as dt
import time
from typing import Iterable

import pandas as pd

from .broker import Account, Position
from .strategy import StrategyConfig, generate_signals


class RealtimeEngine:
    def __init__(self, symbols: Iterable[str], fetcher, interval: int = 60, config: StrategyConfig | None = None):
        self.symbols = list(symbols)
        self.fetcher = fetcher
        self.interval = interval
        self.config = config or StrategyConfig()
        self.account = Account(cash=1_000_000)
        self.buffers = {symbol: pd.DataFrame() for symbol in self.symbols}

    def run_forever(self) -> None:
        print("Starting realtime engine... Press Ctrl+C to stop.")
        try:
            while True:
                self._poll_once()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("Stopped realtime engine.")

    def _poll_once(self) -> None:
        snapshot_df = self.fetcher(self.symbols)
        if snapshot_df.empty:
            print("No snapshot data returned; check network or symbols.")
            return
        ts = dt.datetime.now()
        for _, row in snapshot_df.iterrows():
            symbol = row["代码"]
            price = float(row["最新价"])
            amount = float(row.get("成交额", 0))
            buffer = self.buffers[symbol]
            bar = pd.DataFrame(
                {
                    "open": [price],
                    "high": [price],
                    "low": [price],
                    "close": [price],
                    "volume": [row.get("成交量", 0)],
                    "amount": [amount],
                },
                index=[ts],
            )
            buffer = pd.concat([buffer, bar]).tail(max(self.config.ramp_window * 4, 20))
            self.buffers[symbol] = buffer
            if len(buffer) < max(self.config.ramp_window * 4, 20):
                continue

            # At least one full lookback window collected; evaluate the strategy.
            state = {
                "position": self.account.positions.get(symbol, Position()).qty,
                "cost": self.account.positions.get(symbol, Position()).cost,
            }
            signal = generate_signals(buffer, state, self.config)
            if signal.action == "buy" and signal.qty > 0:
                try:
                    self.account.buy(symbol, signal.qty, signal.price)
                    print(f"BUY {symbol} {signal.qty} @ {signal.price:.2f}")
                except ValueError as exc:
                    print(f"Buy skipped: {exc}")
            elif signal.action == "sell" and signal.qty > 0:
                try:
                    self.account.sell(symbol, signal.qty, signal.price)
                    print(f"SELL {symbol} {signal.qty} @ {signal.price:.2f}")
                except ValueError as exc:
                    print(f"Sell skipped: {exc}")

        summary = self.account.total_value({s: float(snapshot_df.set_index("代码").loc[s]["最新价"]) for s in self.symbols})
        print(f"[{ts}] Equity: {summary:.2f}")
