"""
Basic momentum + volume confirmation strategy for quick ramp-up detection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class Signal:
    action: str  # "buy", "sell", "hold"
    price: float
    qty: int


@dataclass
class StrategyConfig:
    ramp_window: int = 5
    ramp_threshold: float = 0.015
    volume_ratio: float = 1.5
    stop_gain: float = 0.01
    stop_loss: float = -0.005
    lot: int = 500


def generate_signals(df: pd.DataFrame, state: Dict[str, float], config: StrategyConfig | None = None) -> Signal:
    config = config or StrategyConfig()
    last = df.iloc[-1]
    window = df.tail(config.ramp_window)
    ret = window["close"].pct_change().add(1).prod() - 1
    vol_ratio = window["amount"].mean() / df["amount"].tail(max(config.ramp_window * 4, 20)).mean()

    signal = Signal(action="hold", price=float(last["close"]), qty=0)

    if ret > config.ramp_threshold and vol_ratio > config.volume_ratio:
        signal = Signal(action="buy", price=float(last["close"]), qty=int(config.lot))
    else:
        position = state.get("position", 0)
        cost = state.get("cost", float(last["close"]))
        if position > 0:
            pnl = (float(last["close"]) - cost) / cost
            if pnl >= config.stop_gain or pnl <= config.stop_loss:
                signal = Signal(action="sell", price=float(last["close"]), qty=int(position))
    return signal
