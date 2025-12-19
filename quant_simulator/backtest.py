"""
Minute-level backtester driving the strategy and broker.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import pandas as pd

from .broker import Account, Position
from .strategy import StrategyConfig, generate_signals


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[dict]


def run_backtest(
    symbol: str,
    data: pd.DataFrame,
    init_cash: float = 1_000_000,
    config: StrategyConfig | None = None,
) -> BacktestResult:
    if data.empty:
        # Surface an explicit empty result so callers can report data issues clearly.
        return BacktestResult(equity_curve=pd.Series(dtype=float), trades=[])

    account = Account(cash=init_cash)
    config = config or StrategyConfig()
    equity: Dict[pd.Timestamp, float] = {}

    for ts, _ in data.iterrows():
        window = data.loc[:ts].tail(max(config.ramp_window * 4, 20))
        state = {
            "position": account.positions.get(symbol, Position()).qty,
            "cost": account.positions.get(symbol, Position()).cost,
        }
        signal = generate_signals(window, state, config)
        if signal.action == "buy" and signal.qty > 0:
            try:
                account.buy(symbol, signal.qty, signal.price)
            except ValueError:
                pass  # skip if not enough cash
        elif signal.action == "sell" and signal.qty > 0:
            try:
                account.sell(symbol, signal.qty, signal.price)
            except ValueError:
                pass  # skip if not enough qty

        equity[ts] = account.total_value({symbol: window.iloc[-1]["close"]})

    equity_curve = pd.Series(equity)
    trades = [t.__dict__ for t in account.trades]
    return BacktestResult(equity_curve=equity_curve, trades=trades)


def batch_backtest(symbols: Iterable[str], loader, start: str, end: str, period: str = "5m") -> Dict[str, BacktestResult]:
    results: Dict[str, BacktestResult] = {}
    for symbol in symbols:
        data = loader(symbol, start, end, period)
        results[symbol] = run_backtest(symbol, data)
    return results
