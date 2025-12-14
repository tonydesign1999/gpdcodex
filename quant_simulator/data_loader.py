"""
Data loading helpers using AkShare with optional local caching.
"""
from __future__ import annotations

import pathlib
from typing import Iterable

import pandas as pd

CACHE_DIR = pathlib.Path("data_cache")
CACHE_DIR.mkdir(exist_ok=True)


def _ensure_akshare():
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(
            "AkShare is required for data loading. Install with `pip install akshare`"
        ) from exc
    return ak


def _normalize_period(period: str) -> str:
    """Map human-friendly values like "5m" to AkShare's expected format.

    AkShare's ``stock_zh_a_hist`` expects minute periods such as ``"1"`` or
    ``"5"`` rather than ``"1m"``/``"5m"``. Keep daily/weekly/monthly strings
    unchanged so the caller can still pass through those values if needed.
    """

    if period.endswith("m") and period[:-1].isdigit():
        return period[:-1]
    return period


def load_minute_history(symbol: str, start: str, end: str, period: str = "5m") -> pd.DataFrame:
    """
    Load minute-level history for a single symbol.

    Args:
        symbol: Stock code, e.g. "600000".
        start: Start date YYYYMMDD.
        end: End date YYYYMMDD.
        period: One of "1m", "5m" etc. AkShare maps to "1" or "5".

    Returns:
        DataFrame indexed by datetime with OHLCV and amount.
    """
    ak = _ensure_akshare()
    ak_period = _normalize_period(period)
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period=ak_period,
        start_date=start,
        end_date=end,
        adjust="qfq",
    )
    if df is None or df.empty:
        # Return an empty DataFrame with expected columns so downstream code can handle gracefully.
        return pd.DataFrame(
            columns=["open", "high", "low", "close", "volume", "amount"], dtype=float
        )

    df.columns = [
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "amount",
        "pct_chg",
        "turnover",
    ]
    df["datetime"] = pd.to_datetime(df["date"])
    df = df.set_index("datetime").sort_index()
    return df[["open", "high", "low", "close", "volume", "amount"]]


def load_spot(symbols: Iterable[str]) -> pd.DataFrame:
    """
    Load latest spot snapshot for a list of symbols.
    """
    ak = _ensure_akshare()
    spot = ak.stock_zh_a_spot_em()
    return spot[spot["代码"].isin(list(symbols))].copy()


def cache_minute_history(symbol: str, start: str, end: str, period: str = "5m") -> pathlib.Path:
    """
    Download and cache minute history to a parquet file.
    """
    df = load_minute_history(symbol, start, end, period)
    cache_path = CACHE_DIR / f"{symbol}_{period}_{start}_{end}.parquet"
    df.to_parquet(cache_path)
    return cache_path


def load_cached(path: pathlib.Path) -> pd.DataFrame:
    """Load cached parquet file into a DataFrame."""
    return pd.read_parquet(path)
