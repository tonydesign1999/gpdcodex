"""Momentum follow strategy built on minute bars."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from account.broker import Position


@dataclass
class MomentumConfig:
    lookback: int = 5
    return_threshold: float = 0.01
    volume_multiplier: float = 1.5
    take_profit: float = 0.03
    stop_loss: float = 0.02
    decay_lookback: int = 3


class MomentumFollowStrategy:
    def __init__(self, config: MomentumConfig) -> None:
        self.config = config

    def _recent_return(self, df: pd.DataFrame) -> float:
        if len(df) < self.config.lookback:
            return 0.0
        window = df.tail(self.config.lookback)
        start = window.iloc[0]["close"]
        end = window.iloc[-1]["close"]
        return (end - start) / start if start else 0.0

    def _volume_ratio(self, df: pd.DataFrame) -> float:
        if "volume" not in df.columns or len(df) < self.config.lookback * 2:
            return 0.0
        recent = df.tail(self.config.lookback)["volume"].mean()
        base = df.tail(self.config.lookback * 2)["volume"].iloc[: self.config.lookback].mean()
        return recent / base if base else 0.0

    def _momentum_decay(self, df: pd.DataFrame) -> bool:
        if len(df) < self.config.decay_lookback + 1:
            return False
        window = df.tail(self.config.decay_lookback + 1)
        return window["close"].iloc[-1] < window["close"].iloc[0]

    def generate_signal(self, symbol: str, df: pd.DataFrame, position: Optional[Position]) -> str:
        """Return BUY/SELL/HOLD based on momentum conditions."""

        if df.empty or "close" not in df.columns:
            return "HOLD"

        last_price = df.iloc[-1]["close"]
        recent_return = self._recent_return(df)
        vol_ratio = self._volume_ratio(df)

        if position is None or position.quantity == 0:
            if recent_return >= self.config.return_threshold and vol_ratio >= self.config.volume_multiplier:
                return "BUY"
            return "HOLD"

        pnl = (last_price - position.avg_cost) / position.avg_cost if position.avg_cost else 0.0
        if pnl >= self.config.take_profit or pnl <= -self.config.stop_loss:
            return "SELL"

        if self._momentum_decay(df):
            return "SELL"

        return "HOLD"


__all__ = ["MomentumConfig", "MomentumFollowStrategy"]
