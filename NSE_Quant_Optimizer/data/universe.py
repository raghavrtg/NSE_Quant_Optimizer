"""
Asset universe helpers for the NSE Quant Risk Terminal.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from config.settings import ASSET_UNIVERSE, TICKER_LABELS


def flatten_universe(
    selected_categories: Optional[List[str]] = None,
) -> List[str]:
    """
    Return a deduplicated list of tickers from the predefined universe.

    Parameters
    ----------
    selected_categories:
        Optional subset of category names. If None, all categories are included.
    """
    tickers: List[str] = []
    categories = selected_categories or list(ASSET_UNIVERSE.keys())
    for cat in categories:
        tickers.extend(ASSET_UNIVERSE.get(cat, []))
    # Preserve order while removing duplicates.
    seen = set()
    ordered: List[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            ordered.append(t)
    return ordered


def get_category_for_ticker(ticker: str) -> Optional[str]:
    """Return the category name that owns ``ticker``, or None."""
    for cat, members in ASSET_UNIVERSE.items():
        if ticker in members:
            return cat
    return None


def display_name(ticker: str) -> str:
    """Human-readable label for a ticker; falls back to bare symbol."""
    return TICKER_LABELS.get(ticker, ticker.replace(".NS", ""))


def categorize_selection(tickers: List[str]) -> Dict[str, List[str]]:
    """Group a ticker list back into universe categories plus Custom."""
    grouped: Dict[str, List[str]] = {c: [] for c in ASSET_UNIVERSE}
    grouped["Custom"] = []
    for t in tickers:
        cat = get_category_for_ticker(t)
        if cat is None:
            grouped["Custom"].append(t)
        else:
            grouped[cat].append(t)
    return {k: v for k, v in grouped.items() if v}
