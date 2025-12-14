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
    def __init__(
        self,
        symbols: Iterable[str],
        fetcher,
        interval: int = 60,
        config: StrategyConfig | None = None,
        require_confirm: bool = False,
    ):
        self.symbols = list(symbols)
        self.fetcher = fetcher
        self.interval = interval
        self.config = config or StrategyConfig()
        self.account = Account(cash=1_000_000)
        self.buffers = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.require_confirm = require_confirm

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
            self._print_tracking(symbol, price, signal, buffer)
            if signal.action == "buy" and signal.qty > 0:
                if not self._confirm(f"下单买入 {symbol} 数量 {signal.qty} 价格 {signal.price:.2f}？"):
                    print("已取消本次买入。")
                    continue
                try:
                    self.account.buy(symbol, signal.qty, signal.price)
                    print(f"BUY {symbol} {signal.qty} @ {signal.price:.2f}")
                except ValueError as exc:
                    print(f"Buy skipped: {exc}")
            elif signal.action == "sell" and signal.qty > 0:
                if not self._confirm(f"下单卖出 {symbol} 数量 {signal.qty} 价格 {signal.price:.2f}？"):
                    print("已取消本次卖出。")
                    continue
                try:
                    self.account.sell(symbol, signal.qty, signal.price)
                    print(f"SELL {symbol} {signal.qty} @ {signal.price:.2f}")
                except ValueError as exc:
                    print(f"Sell skipped: {exc}")

        summary = self.account.total_value({s: float(snapshot_df.set_index("代码").loc[s]["最新价"]) for s in self.symbols})
        print(f"[{ts}] Equity: {summary:.2f}")

    def _confirm(self, message: str) -> bool:
        if not self.require_confirm:
            return True
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in {"y", "yes", "是", "好"}

    def _print_tracking(self, symbol: str, price: float, signal, buffer: pd.DataFrame) -> None:
        recent_ret = (buffer["close"].iloc[-self.config.ramp_window :]  # noqa: E203
            .pct_change()
            .add(1)
            .prod()
            - 1)
        vol_ratio = (
            buffer["amount"].tail(self.config.ramp_window).mean()
            / buffer["amount"].tail(max(self.config.ramp_window * 4, 20)).mean()
        )
        print(
            f"[{dt.datetime.now()}] 跟踪 {symbol} 现价 {price:.2f} | 短期涨幅 {recent_ret*100:.2f}% "
            f"| 放量倍数 {vol_ratio:.2f} | 信号: {signal.action} 数量 {signal.qty}"
        )


def print_strategy_overview() -> None:
    print("当前量化策略（中文说明）：")
    print(
        "- 监控目标股票的分钟级最新价与成交额，寻找短时间拉升。\n"
        "- 条件：最近配置窗口（默认5根）内的复合涨幅超过阈值（默认1.5%），且成交额均值/更长窗口均值大于放量倍数（默认1.5倍）。\n"
        "- 满足条件时买入固定手数（默认每次500股）。\n"
        "- 若持仓浮盈达到止盈线（默认+1%）或浮亏触及止损线（默认-0.5%），则卖出全部持仓。\n"
        "- 所有买入遵守T+1约束：当日买入的数量冻结，次日才能卖出。\n"
        "- 模拟交易包含滑点与手续费，用于更加接近真实成交。"
    )
