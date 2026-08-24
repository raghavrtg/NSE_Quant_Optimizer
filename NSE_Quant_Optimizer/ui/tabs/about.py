"""
Tab 6 — About & Institutional Methodology.
"""

from __future__ import annotations

import streamlit as st

from config.settings import RISK_FREE_RATE, TRADING_DAYS


def render_about_tab() -> None:
    st.subheader("About & Institutional Methodology")
    st.markdown(
        f"""
### NSE Quant Risk Terminal

An analytical education platform for **Indian capital markets** covering NSE
equities, index/factor ETFs, gold & silver ETFs, gilt / liquid funds, and
REIT / InvIT yield instruments.

#### Architecture
- **Data:** `yfinance` adjusted closes with `@st.cache_data(ttl=3600)` caching.
- **Moments:** Daily log returns → annualized means (×{TRADING_DAYS}) and
  Ledoit–Wolf shrinkage covariance.
- **Optimization:** `scipy.optimize.minimize` (SLSQP), long-only, Σw = 1.
- **Risk:** Parametric & historical VaR, CVaR, Max Drawdown, Sortino, Sharpe
  (r<sub>f</sub> = {RISK_FREE_RATE:.2%}).
- **Forward simulation:** Vectorized GBM Monte Carlo (5,000–10,000 paths).
- **Allocator:** Rule-based lifecycle risk-parity questionnaire → Equity /
  Debt / Gold / REITs mix, mapped onto the selected ticker sleeve.

#### Session Privacy
All user inputs, custom weights, questionnaire answers, and simulation seeds
live exclusively in **Streamlit session state** for the active browser session.
There is no shared database and **zero cross-user visibility**.

#### Statutory Notice
This platform does **not** constitute SEBI-registered investment advisory,
portfolio management, or a solicitation to buy/sell securities. Quantitative
outputs are model-based and educational. Past performance is non-indicative of
future market outcomes.
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Technology Stack")
    st.code(
        "Streamlit · Plotly · Pandas · NumPy · SciPy · scikit-learn · yfinance · Pillow",
        language="text",
    )
