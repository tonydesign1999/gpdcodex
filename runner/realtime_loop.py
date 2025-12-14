"""Realtime trading loop that wires data, strategy and broker together."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, Optional

import pandas as pd
import schedule

from account.broker import Broker
from data.akshare_client import AkshareClient
from storage.logger import CsvSqliteLogger
from strategy.momentum_follow import MomentumFollowStrategy


class RealtimeRunner:
    def __init__(
        self,
        symbols: Iterable[str],
        client: AkshareClient,
        strategy: MomentumFollowStrategy,
        broker: Broker,
        logger: Optional[CsvSqliteLogger] = None,
        bar_period: str = "1",
    ) -> None:
        self.symbols = list(symbols)
        self.client = client
        self.strategy = strategy
        self.broker = broker
        self.logger = logger
        self.bar_period = bar_period

    def _log_market(self, symbol: str, bars: pd.DataFrame) -> None:
        if self.logger:
            self.logger.log_market_data(symbol, bars.tail(1))

    def _log_signal(self, symbol: str, signal: str, price: float) -> None:
        if self.logger:
            self.logger.log_signal({"symbol": symbol, "signal": signal, "price": price, "timestamp": datetime.now()})

    def _log_fill(self, fill) -> None:
        if self.logger and fill:
            self.logger.log_fill(fill)

    def _log_account(self) -> None:
        if self.logger:
            snapshot = self.broker.mark_to_market({})
            self.logger.log_account(snapshot)

    def run_once(self) -> None:
        now = datetime.now()
        self.broker.rollover(now.date())
        for symbol in self.symbols:
            bars = self.client.get_minute_bars(symbol=symbol, period=self.bar_period)
            if bars.empty:
                continue
            last_price = float(bars.iloc[-1]["close"])
            self._log_market(symbol, bars)
            signal = self.strategy.generate_signal(symbol, bars, self.broker.positions.get(symbol))
            self._log_signal(symbol, signal, last_price)
            fill = None
            if signal == "BUY":
                qty = max(1, int(self.broker.cash // last_price // 100) * 100)
                fill = self.broker.buy(symbol, last_price, qty, trading_date=now.date())
            elif signal == "SELL":
                pos = self.broker.positions.get(symbol)
                qty = pos.available if pos else 0
                fill = self.broker.sell(symbol, last_price, qty, trading_date=now.date())
            if fill:
                self._log_fill(fill)
        self._log_account()

    def start(self, interval_seconds: int = 60) -> None:
        schedule.clear()
        schedule.every(interval_seconds).seconds.do(self.run_once)
        while True:
            schedule.run_pending()


__all__ = ["RealtimeRunner"]
