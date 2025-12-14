"""Historical replay utilities for validating momentum parameters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from account.broker import Broker
from data.akshare_client import AkshareClient
from strategy.momentum_follow import MomentumConfig, MomentumFollowStrategy


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    annualized_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    trades: int


class MomentumReplayer:
    def __init__(
        self,
        symbols: Iterable[str],
        client: AkshareClient,
        strategy_config: MomentumConfig,
        broker: Broker,
    ) -> None:
        self.symbols = list(symbols)
        self.client = client
        self.strategy = MomentumFollowStrategy(strategy_config)
        self.broker = broker

    def _iter_bars(self, symbol: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
        df = self.client.get_minute_bars(symbol, period="1", start_time=start, end_time=end)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime")
        return df

    def run(self, start: Optional[str] = None, end: Optional[str] = None) -> BacktestResult:
        equity_records: List[float] = []
        equity_index: List[pd.Timestamp] = []
        wins = 0

        for symbol in self.symbols:
            df = self._iter_bars(symbol, start, end)
            if df.empty:
                continue
            for idx in range(len(df)):
                window = df.iloc[: idx + 1]
                bar_time = window.iloc[-1]["datetime"] if "datetime" in window.columns else datetime.now()
                trading_date = bar_time.date() if isinstance(bar_time, (pd.Timestamp, datetime)) else date.today()
                self.broker.rollover(trading_date)
                signal = self.strategy.generate_signal(symbol, window, self.broker.positions.get(symbol))
                price = float(window.iloc[-1]["close"])
                if signal == "BUY":
                    qty = max(1, int(self.broker.cash // price // 100) * 100)
                    self.broker.buy(symbol, price, qty, trading_date=trading_date)
                elif signal == "SELL":
                    pos = self.broker.positions.get(symbol)
                    qty = pos.available if pos else 0
                    if pos and pos.avg_cost > 0 and price > pos.avg_cost:
                        wins += 1
                    self.broker.sell(symbol, price, qty, trading_date=trading_date)
                snapshot = self.broker.mark_to_market({symbol: price})
                equity_records.append(snapshot.equity)
                equity_index.append(pd.to_datetime(bar_time))

        equity_series = pd.Series(equity_records, index=equity_index).sort_index()
        returns = equity_series.pct_change().dropna()
        days = (equity_series.index[-1] - equity_series.index[0]).days or 1
        annualized_return = (equity_series.iloc[-1] / equity_series.iloc[0]) ** (365 / days) - 1
        sharpe = np.sqrt(252) * returns.mean() / returns.std() if not returns.empty else 0.0
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min() if not drawdown.empty else 0.0
        trades = len(self.broker.trade_log)
        win_rate = wins / trades if trades else 0.0

        return BacktestResult(
            equity_curve=equity_series,
            annualized_return=annualized_return,
            sharpe=sharpe,
            max_drawdown=float(max_drawdown),
            win_rate=win_rate,
            trades=trades,
        )


__all__ = ["BacktestResult", "MomentumReplayer"]
