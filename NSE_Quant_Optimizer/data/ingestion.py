"""
Market data ingestion via yfinance with Streamlit caching.

All downloads are isolated per Streamlit session; cached payloads expire
after one hour so intraday users pick up refreshed OHLCV without hammering
the Yahoo endpoint on every widget interaction.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st
import yfinance as yf

logger = logging.getLogger(__name__)


def _normalize_nse_ticker(symbol: str) -> str:
    """Ensure an NSE equity / ETF symbol carries the ``.NS`` suffix."""
    raw = symbol.strip().upper()
    if not raw:
        raise ValueError("Ticker symbol cannot be empty.")
    if raw.endswith(".NS") or raw.endswith(".BO"):
        return raw
    return f"{raw}.NS"


@st.cache_data(ttl=3600, show_spinner=False)
def validate_nse_ticker(symbol: str) -> Tuple[bool, str, str]:
    """
    Probe Yahoo Finance for a single NSE ticker.

    Returns
    -------
    (ok, normalized_ticker, message)
        ``ok`` is True when at least one adjusted-close observation exists.
    """
    try:
        ticker = _normalize_nse_ticker(symbol)
    except ValueError as exc:
        return False, symbol, str(exc)

    try:
        hist = yf.Ticker(ticker).history(period="5d", auto_adjust=True)
        if hist is None or hist.empty or "Close" not in hist.columns:
            return False, ticker, f"No price data found for '{ticker}'. Verify the NSE symbol."
        return True, ticker, f"Validated: {ticker}"
    except Exception as exc:  # noqa: BLE001 — surface vendor errors cleanly
        logger.exception("Ticker validation failed for %s", ticker)
        return False, ticker, f"Lookup failed for '{ticker}': {exc}"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(
    tickers: Tuple[str, ...],
    lookback_years: int = 3,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Download adjusted close prices for one or more NSE tickers.

    Parameters
    ----------
    tickers:
        Immutable tuple of Yahoo-style tickers (e.g. ``RELIANCE.NS``). Tuple
        typing is required for Streamlit cache key stability.
    lookback_years:
        Calendar years of history to request.
    end_date:
        Optional ISO date string; defaults to today (UTC-ish local).

    Returns
    -------
    DataFrame
        Columns are tickers; index is DatetimeIndex of trading days.
        Tickers with completely missing history are dropped. Partially missing
        series are forward/back-filled then any remaining NaNs dropped pairwise.
    """
    if not tickers:
        raise ValueError("At least one ticker is required.")

    normalized = [_normalize_nse_ticker(t) for t in tickers]
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
    start = end - timedelta(days=int(lookback_years * 365.25))

    try:
        raw = yf.download(
            tickers=list(normalized),
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by="column",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("yfinance download failed")
        raise RuntimeError(f"Market data download failed: {exc}") from exc

    if raw is None or raw.empty:
        raise RuntimeError(
            "No market data returned. Check ticker symbols and network connectivity."
        )

    prices = _extract_close(raw, normalized)
    if prices.empty:
        raise RuntimeError("Could not extract Close prices from the downloaded payload.")

    # Drop columns that are entirely NaN (delisted / bad symbol).
    valid = prices.dropna(axis=1, how="all")
    dropped = [c for c in prices.columns if c not in valid.columns]
    if dropped:
        logger.warning("Dropped tickers with no history: %s", dropped)

    if valid.empty:
        raise RuntimeError("All selected tickers returned empty price histories.")

    # Align on common trading calendar; light fill for isolated gaps only.
    cleaned = valid.sort_index().ffill(limit=3).bfill(limit=3)
    cleaned = cleaned.dropna(how="any")

    if cleaned.empty or len(cleaned) < 60:
        raise RuntimeError(
            "Insufficient overlapping history after cleaning "
            f"({len(cleaned)} rows). Widen the lookback or remove illiquid names."
        )

    return cleaned


def _extract_close(raw: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
    """Normalize yfinance multi-index / single-ticker layouts to Close columns."""
    if isinstance(raw.columns, pd.MultiIndex):
        # Prefer Adj Close if present; else Close (auto_adjust=True usually collapses).
        level0 = raw.columns.get_level_values(0)
        if "Close" in level0:
            close = raw["Close"].copy()
        elif "Adj Close" in level0:
            close = raw["Adj Close"].copy()
        else:
            # Sometimes fields are the second level.
            level1 = raw.columns.get_level_values(1)
            if "Close" in level1:
                close = raw.xs("Close", axis=1, level=1).copy()
            else:
                raise RuntimeError("Download payload missing Close / Adj Close fields.")
        # Ensure column order matches request where possible.
        available = [t for t in tickers if t in close.columns]
        extras = [c for c in close.columns if c not in available]
        return close[available + extras]
    # Single ticker → flat columns.
    if "Close" in raw.columns:
        series = raw["Close"].rename(tickers[0])
        return series.to_frame()
    if "Adj Close" in raw.columns:
        series = raw["Adj Close"].rename(tickers[0])
        return series.to_frame()
    raise RuntimeError("Unexpected yfinance column layout.")
