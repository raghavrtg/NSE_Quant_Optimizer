"""
Central configuration for the NSE Quantitative Portfolio Risk Terminal.

All rates, asset universes, theme tokens, and simulation defaults live here
so the rest of the codebase remains free of magic numbers.
"""

from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# Market & optimization constants
# ---------------------------------------------------------------------------

# Benchmark risk-free rate aligned with RBI repo / 10-yr G-Sec context (~6.75%).
RISK_FREE_RATE: float = 0.0675

# NSE equity trading-day convention for annualization.
TRADING_DAYS: int = 252

DEFAULT_LOOKBACK_YEARS: int = 3
FRONTIER_POINTS: int = 50

MC_PATHS_MIN: int = 5_000
MC_PATHS_MAX: int = 10_000
MC_PATHS_DEFAULT: int = 7_500
MC_HORIZON_MIN: int = 30
MC_HORIZON_MAX: int = 365
MC_HORIZON_DEFAULT: int = 252

# ---------------------------------------------------------------------------
# Predefined NSE asset universe (yfinance tickers use .NS suffix)
# ---------------------------------------------------------------------------

ASSET_UNIVERSE: Dict[str, List[str]] = {
    "Large Cap Bluechips": [
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "INFY.NS",
        "ICICIBANK.NS",
        "ITC.NS",
        "LT.NS",
        "BHARTIARTL.NS",
    ],
    "Index & Factor ETFs": [
        "NIFTYBEES.NS",
        "JUNIORBEES.NS",
        "MID150BEES.NS",
        "BANKBEES.NS",
    ],
    "Commodities & Fixed Income ETFs": [
        "GOLDBEES.NS",
        "SILVERBEES.NS",
        "SETF10GILT.NS",
        "LIQUIDBEES.NS",
    ],
    "Yield Instruments (REITs & InvITs)": [
        "EMBASSY.NS",
        "MINDSPACE.NS",
        "BIRET.NS",
        "PGINVIT.NS",
    ],
}

# Human-readable labels for display (ticker without .NS where useful).
TICKER_LABELS: Dict[str, str] = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ICICIBANK.NS": "ICICI Bank",
    "ITC.NS": "ITC",
    "LT.NS": "Larsen & Toubro",
    "BHARTIARTL.NS": "Bharti Airtel",
    "NIFTYBEES.NS": "Nifty 50 ETF",
    "JUNIORBEES.NS": "Nifty Next 50 ETF",
    "MID150BEES.NS": "Nifty Midcap 150 ETF",
    "BANKBEES.NS": "Bank Nifty ETF",
    "GOLDBEES.NS": "Physical Gold ETF",
    "SILVERBEES.NS": "Silver ETF",
    "SETF10GILT.NS": "10-Yr G-Sec ETF",
    "LIQUIDBEES.NS": "Liquid BeES",
    "EMBASSY.NS": "Embassy REIT",
    "MINDSPACE.NS": "Mindspace REIT",
    "BIRET.NS": "Brookfield India REIT",
    "PGINVIT.NS": "PowerGrid InvIT",
}

# Map tickers to broad asset classes for the AI allocator.
TICKER_ASSET_CLASS: Dict[str, str] = {
    "RELIANCE.NS": "Equity",
    "TCS.NS": "Equity",
    "HDFCBANK.NS": "Equity",
    "INFY.NS": "Equity",
    "ICICIBANK.NS": "Equity",
    "ITC.NS": "Equity",
    "LT.NS": "Equity",
    "BHARTIARTL.NS": "Equity",
    "NIFTYBEES.NS": "Equity",
    "JUNIORBEES.NS": "Equity",
    "MID150BEES.NS": "Equity",
    "BANKBEES.NS": "Equity",
    "GOLDBEES.NS": "Gold",
    "SILVERBEES.NS": "Gold",
    "SETF10GILT.NS": "Debt",
    "LIQUIDBEES.NS": "Debt",
    "EMBASSY.NS": "REITs",
    "MINDSPACE.NS": "REITs",
    "BIRET.NS": "REITs",
    "PGINVIT.NS": "REITs",
}

# ---------------------------------------------------------------------------
# Theme tokens — Midnight Dark & Clean Institutional Light
# ---------------------------------------------------------------------------

THEME_COLORS: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#0E1117",
        "card": "#1E222D",
        "card_alt": "#262B36",
        "border": "#2A2F3A",
        "text": "#E8EAED",
        "text_muted": "#9AA0A6",
        "accent": "#C8CBD0",
        "positive": "#26A69A",
        "negative": "#EF5350",
        "chart_line": "#A0A4AB",
        "chart_fill": "rgba(160, 164, 171, 0.15)",
        "heatmap_scale": "Greys",
        "banner_overlay": "rgba(14, 17, 23, 0.72)",
    },
    "light": {
        "bg": "#FFFFFF",
        "card": "#F8F9FA",
        "card_alt": "#EEF0F2",
        "border": "#DEE2E6",
        "text": "#1A1D23",
        "text_muted": "#5F6368",
        "accent": "#343A40",
        "positive": "#2E7D32",
        "negative": "#C62828",
        "chart_line": "#495057",
        "chart_fill": "rgba(73, 80, 87, 0.12)",
        "heatmap_scale": "Greys",
        "banner_overlay": "rgba(255, 255, 255, 0.78)",
    },
}

DISCLAIMER_TEXT: str = (
    "Statutory Disclaimer: Quantitative models and projected portfolio returns "
    "are generated via mathematical optimization and historical statistical "
    "simulations. Past performance is non-indicative of future market outcomes. "
    "This platform is an analytical educational tool and does not constitute "
    "SEBI-registered financial advisory."
)

APP_TITLE: str = "NSE Quant Risk Terminal"
APP_SUBTITLE: str = "Institutional Portfolio Optimization & Risk Analytics"
