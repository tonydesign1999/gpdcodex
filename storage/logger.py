"""Utility helpers for persisting market events to disk."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from account.broker import AccountSnapshot, Fill


class CsvSqliteLogger:
    def __init__(self, base_dir: Path | str = Path("logs"), sqlite_path: Optional[Path | str] = None) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        if self.sqlite_path:
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    def _append_csv(self, name: str, df: pd.DataFrame) -> None:
        path = self.base_dir / f"{name}.csv"
        header = not path.exists()
        df.to_csv(path, mode="a", header=header, index=False)

    def _append_sqlite(self, table: str, df: pd.DataFrame) -> None:
        if not self.sqlite_path:
            return
        with sqlite3.connect(self.sqlite_path) as conn:
            df.to_sql(table, conn, if_exists="append", index=False)

    def log_market_data(self, symbol: str, df: pd.DataFrame) -> None:
        enriched = df.copy()
        enriched.insert(0, "symbol", symbol)
        self._append_csv("market_data", enriched)
        self._append_sqlite("market_data", enriched)

    def log_signal(self, record: dict) -> None:
        df = pd.DataFrame([record])
        self._append_csv("signals", df)
        self._append_sqlite("signals", df)

    def log_fill(self, fill: Fill) -> None:
        df = pd.DataFrame([asdict(fill)])
        self._append_csv("fills", df)
        self._append_sqlite("fills", df)

    def log_account(self, snapshot: AccountSnapshot) -> None:
        positions = {sym: asdict(pos) for sym, pos in snapshot.positions.items()}
        record = asdict(snapshot)
        record["positions"] = json.dumps(positions)
        df = pd.DataFrame([record])
        self._append_csv("account", df)
        self._append_sqlite("account", df)


__all__ = ["CsvSqliteLogger"]
