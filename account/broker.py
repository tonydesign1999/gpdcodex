"""Account and execution simulator with T+1 settlement rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    available: int = 0
    avg_cost: float = 0.0
    frozen: int = 0

    def market_value(self, price: float) -> float:
        return price * self.quantity


@dataclass
class Fill:
    symbol: str
    side: str
    price: float
    quantity: int
    fee: float
    timestamp: datetime
    cash_after: float
    position_after: int


@dataclass
class AccountSnapshot:
    timestamp: datetime
    cash: float
    equity: float
    positions: Dict[str, Position] = field(default_factory=dict)


class Broker:
    """Simple broker model supporting T+1, slippage and fees."""

    def __init__(
        self,
        starting_cash: float,
        slippage: float = 0.0005,
        commission_rate: float = 0.0003,
        stamp_duty: float = 0.001,
        min_commission: float = 5.0,
    ) -> None:
        self.cash = starting_cash
        self.slippage = slippage
        self.commission_rate = commission_rate
        self.stamp_duty = stamp_duty
        self.min_commission = min_commission
        self.positions: Dict[str, Position] = {}
        self._current_date: Optional[date] = None
        self.trade_log: List[Fill] = []

    def _commission(self, amount: float, include_tax: bool) -> float:
        fee = max(self.min_commission, amount * self.commission_rate)
        if include_tax:
            fee += amount * self.stamp_duty
        return fee

    def _ensure_position(self, symbol: str) -> Position:
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def rollover(self, trading_date: date) -> None:
        """Release T+1 frozen quantities when the trading day advances."""

        if self._current_date is None:
            self._current_date = trading_date
            return

        if trading_date != self._current_date:
            for pos in self.positions.values():
                pos.available += pos.frozen
                pos.frozen = 0
            self._current_date = trading_date

    def buy(self, symbol: str, price: float, quantity: int, trading_date: date) -> Optional[Fill]:
        self.rollover(trading_date)
        if quantity <= 0:
            return None

        adjusted_price = price * (1 + self.slippage)
        gross = adjusted_price * quantity
        fee = self._commission(gross, include_tax=False)
        total = gross + fee

        if total > self.cash:
            affordable_qty = int(self.cash // adjusted_price)
            quantity = max(0, affordable_qty)
            if quantity == 0:
                return None
            gross = adjusted_price * quantity
            fee = self._commission(gross, include_tax=False)
            total = gross + fee

        self.cash -= total
        pos = self._ensure_position(symbol)
        new_qty = pos.quantity + quantity
        pos.avg_cost = (pos.avg_cost * pos.quantity + gross) / new_qty if new_qty else 0.0
        pos.quantity = new_qty
        pos.frozen += quantity  # T+1

        fill = Fill(
            symbol=symbol,
            side="BUY",
            price=adjusted_price,
            quantity=quantity,
            fee=fee,
            timestamp=datetime.combine(trading_date, datetime.now().time()),
            cash_after=self.cash,
            position_after=pos.quantity,
        )
        self.trade_log.append(fill)
        return fill

    def sell(self, symbol: str, price: float, quantity: int, trading_date: date) -> Optional[Fill]:
        self.rollover(trading_date)
        if quantity <= 0:
            return None

        pos = self.positions.get(symbol)
        if pos is None or pos.available <= 0:
            return None
        quantity = min(quantity, pos.available)

        adjusted_price = price * (1 - self.slippage)
        gross = adjusted_price * quantity
        fee = self._commission(gross, include_tax=True)
        self.cash += gross - fee

        pos.quantity -= quantity
        pos.available -= quantity
        if pos.quantity == 0:
            pos.avg_cost = 0
            pos.available = 0
            pos.frozen = 0

        fill = Fill(
            symbol=symbol,
            side="SELL",
            price=adjusted_price,
            quantity=quantity,
            fee=fee,
            timestamp=datetime.combine(trading_date, datetime.now().time()),
            cash_after=self.cash,
            position_after=pos.quantity,
        )
        self.trade_log.append(fill)
        return fill

    def mark_to_market(self, prices: Dict[str, float]) -> AccountSnapshot:
        equity = self.cash
        for symbol, pos in self.positions.items():
            price = prices.get(symbol, pos.avg_cost)
            equity += pos.market_value(price)
        return AccountSnapshot(
            timestamp=datetime.now(),
            cash=self.cash,
            equity=equity,
            positions={k: Position(**vars(v)) for k, v in self.positions.items()},
        )


__all__ = ["Broker", "Position", "Fill", "AccountSnapshot"]
