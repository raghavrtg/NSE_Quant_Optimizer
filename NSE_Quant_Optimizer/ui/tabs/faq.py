"""
Tab 5 — FAQ & Knowledge Base.
"""

from __future__ import annotations

import streamlit as st


def render_faq_tab() -> None:
    st.subheader("FAQ & Knowledge Base")
    st.caption("Concise institutional primers for the risk metrics used across this terminal.")

    with st.expander("Value at Risk (VaR)", expanded=True):
        st.markdown(
            """
**What it measures.** VaR estimates the loss threshold that will not be exceeded
with a stated confidence over a horizon. A 95% 1-day VaR of 2% means that, under
the model, daily losses should stay within 2% on 95% of days.

**Parametric VaR** assumes (approximately) Gaussian log returns and scales with
√T for multi-day horizons. **Historical VaR** uses the empirical return quantile
and makes fewer distributional assumptions, but is sensitive to the sample window.

**Limitations.** VaR is not coherent (subadditivity can fail) and says nothing
about the severity of losses *beyond* the threshold — that is the role of CVaR.
            """
        )

    with st.expander("Conditional Value at Risk (CVaR / Expected Shortfall)"):
        st.markdown(
            """
**What it measures.** CVaR is the expected loss *conditional* on exceeding the
VaR threshold. It answers: “When things go bad, how bad is the average outcome?”

**Why institutions prefer it.** CVaR is a coherent risk measure and penalizes
tail thickness more faithfully than VaR. This terminal reports 95% and 99%
1-day historical Expected Shortfall on the portfolio return path.
            """
        )

    with st.expander("Sharpe Ratio"):
        st.markdown(
            """
**Definition.** Sharpe = (E[R] − r_f) / σ, where r_f is the risk-free rate
(here 6.75%, reflecting RBI repo / G-Sec context) and σ is annualized volatility.

**Interpretation.** It measures excess return per unit of total volatility.
Higher is better *all else equal*, but Sharpe is silent on drawdowns, skewness,
and liquidity — complement it with Sortino, Max DD, and VaR/CVaR.
            """
        )

    with st.expander("Markowitz Mean–Variance Theory"):
        st.markdown(
            """
**Core idea.** Harry Markowitz formalized diversification: for a given expected
return, minimize portfolio variance (or maximize return for a given variance).
The set of optimal portfolios forms the **efficient frontier**.

**This terminal.** We estimate means from log returns, stabilize the covariance
via Ledoit–Wolf shrinkage, and solve long-only, fully invested problems with
`scipy.optimize.minimize` (SLSQP) for Max Sharpe, Min Variance, and Risk Parity.
            """
        )

    with st.expander("Monte Carlo & Geometric Brownian Motion"):
        st.markdown(
            """
**GBM dynamics.**  
S<sub>t+1</sub> = S<sub>t</sub> · exp((μ − ½σ²)Δt + σ√Δt · Z), Z ∼ N(0,1).

**Usage here.** Drift μ and volatility σ are taken from the active portfolio’s
annualized moments. Thousands of vectorized paths produce P5 / P50 / P95
corridors and the probability that terminal wealth falls below initial capital.

**Caveat.** GBM assumes continuous paths, constant μ/σ, and no jumps — useful for
illustration, not a complete description of NSE crash or gap risk.
            """,
            unsafe_allow_html=True,
        )
