"""
Simple broker and account model respecting T+1 for A-share simulation.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Position:
    qty: int = 0
    frozen: int = 0
    cost: float = 0.0  # weighted average cost


@dataclass
class Trade:
    time: dt.datetime
    symbol: str
    side: str
    qty: int
    price: float
    fee: float


@dataclass
class Account:
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)

    def _update_cost(self, symbol: str, qty: int, price: float) -> None:
        pos = self.positions.setdefault(symbol, Position())
        new_qty = pos.qty + qty
        pos.cost = (pos.cost * pos.qty + price * qty) / new_qty if new_qty else 0.0
        pos.qty = new_qty

    def buy(self, symbol: str, qty: int, price: float, fee_rate: float = 0.0005, slip: float = 0.001) -> None:
        """
        Execute a buy order with simple slip/fee modeling and T+1 freeze.

        Frozen quantity cannot be sold until :py:meth:`unfreeze_daily` is called to simulate T+1.
        """

        trade_price = price * (1 + slip)  # optimistic slip upward on buy
        cost = trade_price * qty
        fee = cost * fee_rate
        if self.cash < cost + fee:
            raise ValueError("Insufficient cash for buy order")
        self.cash -= cost + fee
        self._update_cost(symbol, qty, trade_price)
        # T+1: mark shares bought today as frozen until next session.
        self.positions[symbol].frozen += qty
        self.trades.append(
            Trade(time=dt.datetime.now(), symbol=symbol, side="buy", qty=qty, price=trade_price, fee=fee)
        )

    def sell(self, symbol: str, qty: int, price: float, fee_rate: float = 0.0005, slip: float = 0.001) -> None:
        """Sell only the portion not frozen by T+1, applying slip/fee on proceeds."""

        pos = self.positions.get(symbol, Position())
        sellable = pos.qty - pos.frozen
        if sellable < qty:
            raise ValueError("Not enough sellable qty due to T+1 constraint")
        trade_price = price * (1 - slip)  # pessimistic slip downward on sell
        proceeds = trade_price * qty
        fee = proceeds * fee_rate
        self.cash += proceeds - fee
        pos.qty -= qty
        self.trades.append(
            Trade(time=dt.datetime.now(), symbol=symbol, side="sell", qty=qty, price=trade_price, fee=fee)
        )

    def unfreeze_daily(self) -> None:
        for pos in self.positions.values():
            pos.frozen = 0

    def total_value(self, latest_prices: Dict[str, float]) -> float:
        value = self.cash
        for symbol, pos in self.positions.items():
            value += pos.qty * latest_prices.get(symbol, pos.cost)
        return value
