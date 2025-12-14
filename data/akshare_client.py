"""Utilities for downloading and caching Akshare market data.

The client wraps the Akshare functions used in the project and provides a
local on-disk cache so backtests and real-time loops can reuse data without
hitting the remote API repeatedly. When the remote source is unavailable the
cache will be returned if present.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import akshare as ak
import pandas as pd


class AkshareClient:
    """Lightweight wrapper around Akshare endpoints with file-system caching."""

    def __init__(self, cache_dir: Path | str = Path("data/cache")) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.spot_cache = self.cache_dir / "spot_cache.csv"

    def _filter_symbols(self, df: pd.DataFrame, symbols: Iterable[str]) -> pd.DataFrame:
        symbols_set = {s.lower() for s in symbols}
        for column in ("代码", "symbol", "Symbol", "code"):
            if column in df.columns:
                filtered = df[df[column].str.lower().isin(symbols_set)]
                if not filtered.empty:
                    return filtered
        return df

    def get_spot_quotes(self, symbols: Iterable[str], use_cache: bool = True) -> pd.DataFrame:
        """Fetch spot quotes for a list of A-share symbols."""

        def _load_cache() -> Optional[pd.DataFrame]:
            if use_cache and self.spot_cache.exists():
                return pd.read_csv(self.spot_cache)
            return None

        try:
            spot_df = ak.stock_zh_a_spot()
            filtered = self._filter_symbols(spot_df, symbols)
            filtered.to_csv(self.spot_cache, index=False)
            return filtered
        except Exception:
            cached = _load_cache()
            if cached is not None:
                return self._filter_symbols(cached, symbols)
            raise

    def get_minute_bars(
        self,
        symbol: str,
        period: str = "1",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch intraday minute bars and store them locally."""

        cache_file = self.cache_dir / f"{symbol}_min_{period}.csv"
        cached_df: Optional[pd.DataFrame] = None
        if use_cache and cache_file.exists():
            cached_df = pd.read_csv(cache_file, parse_dates=["datetime"], infer_datetime_format=True)

        request_start = start_time
        if cached_df is not None and not cached_df.empty:
            last_timestamp = cached_df["datetime"].max()
            request_start = (last_timestamp + pd.Timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            fresh_df = ak.stock_zh_a_hist_min_em(
                symbol=symbol,
                start_date=request_start,
                end_date=end_time,
                period=period,
            )
            if not fresh_df.empty:
                fresh_df.rename(columns={"日期": "datetime", "时间": "datetime"}, inplace=True)
                fresh_df["datetime"] = pd.to_datetime(fresh_df["datetime"])
                merged = fresh_df if cached_df is None else pd.concat([cached_df, fresh_df], ignore_index=True)
            else:
                merged = cached_df if cached_df is not None else fresh_df

            if merged is None or merged.empty:
                raise RuntimeError(f"No data available for symbol {symbol}")

            merged = merged.drop_duplicates(subset=["datetime"]).sort_values("datetime")
            merged.to_csv(cache_file, index=False)
            return merged
        except Exception:
            if cached_df is not None:
                return cached_df
            raise

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Return the latest cached price when available."""

        cache_file = self.cache_dir / f"{symbol}_min_1.csv"
        if not cache_file.exists():
            return None
        df = pd.read_csv(cache_file)
        if df.empty or "close" not in df.columns:
            return None
        return float(df.iloc[-1]["close"])


__all__ = ["AkshareClient"]
