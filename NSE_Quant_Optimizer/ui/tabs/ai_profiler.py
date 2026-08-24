"""
Tab 4 — AI Profiler & Custom Scenario Stress-Testing.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import streamlit as st

from allocator.advisor import (
    apply_stress_shock,
    map_advice_to_tickers,
    recommend_allocation,
)
from config.settings import RISK_FREE_RATE
from quant.returns import ReturnStatistics, portfolio_moments
from quant.risk_metrics import compute_portfolio_risk_metrics
from ui.charts import asset_class_pie, weights_bar_figure
from ui.components import fmt_num, fmt_pct, render_metric_row


def render_ai_profiler_tab(
    stats: ReturnStatistics,
    portfolio_ctx: Dict[str, Any],
) -> None:
    st.subheader("AI Allocation Advisor")
    st.caption(
        "Rule-based lifecycle risk-parity engine. Recommendations are educational "
        "baselines — not personalized SEBI-registered advice."
    )

    q1, q2 = st.columns(2)
    with q1:
        age = st.slider("Age", 18, 80, 35, key="adv_age")
        horizon = st.slider("Investment Horizon (Years)", 1, 40, 10, key="adv_horizon")
    with q2:
        risk_tol = st.selectbox(
            "Risk Tolerance",
            ["Capital Preservation", "Conservative", "Moderate", "Aggressive"],
            index=2,
            key="adv_risk",
        )
        objective = st.selectbox(
            "Primary Objective",
            ["Wealth Creation", "Retirement", "Regular Income"],
            index=0,
            key="adv_obj",
        )

    advice = recommend_allocation(age, horizon, risk_tol, objective)

    render_metric_row(
        [
            ("Risk Score", f"{advice.risk_score:.0f}/100", advice.profile_label, None),
            ("Equity", fmt_pct(advice.equity), None, True),
            ("Debt / G-Sec", fmt_pct(advice.debt), None, None),
            ("Gold", fmt_pct(advice.gold), None, None),
            ("REITs / InvITs", fmt_pct(advice.reits), None, None),
        ]
    )
    st.info(advice.rationale)

    pie_col, map_col = st.columns([1, 1.2])
    with pie_col:
        st.plotly_chart(asset_class_pie(advice.as_series()), use_container_width=True)

    tickers = list(stats.mean_annual.index)
    advisor_w = map_advice_to_tickers(advice, tickers)
    with map_col:
        st.plotly_chart(weights_bar_figure(advisor_w, "Mapped Ticker Sleeve"), use_container_width=True)

    if st.button("Apply Advisor Weights to Manual Sliders", key="apply_advisor"):
        st.session_state.manual_weights = advisor_w.copy()
        # Sync slider widget keys (0–100 percent space).
        for t, v in advisor_w.items():
            st.session_state[f"w_{t}"] = float(v) * 100.0
        st.success("Advisor weights applied. Return to Tab 1 to inspect updated metrics.")
        st.rerun()

    st.markdown("---")
    st.subheader("Custom Scenario Stress-Testing")
    st.caption(
        "Shock expected returns and inflate covariances by asset class, then "
        "recompute portfolio moments under the active manual weights."
    )

    s1, s2, s3 = st.columns(3)
    with s1:
        eq_shock = st.slider("Equity Return Shock", -0.50, 0.20, -0.20, 0.01, key="stress_eq")
    with s2:
        rate_shock = st.slider("Rates Shock (abs)", 0.0, 0.05, 0.01, 0.005, key="stress_rate")
    with s3:
        gold_shock = st.slider("Gold Return Shock", -0.20, 0.30, 0.05, 0.01, key="stress_gold")

    weights = (
        portfolio_ctx.get("manual_weights")
        if portfolio_ctx
        else pd.Series(1.0 / len(tickers), index=tickers)
    )
    if weights is None:
        weights = advisor_w

    shocked_mu, shocked_cov = apply_stress_shock(
        stats.mean_annual,
        stats.cov_annual,
        equity_shock=float(eq_shock),
        rates_shock=float(rate_shock),
        gold_shock=float(gold_shock),
    )
    base = portfolio_moments(weights.values, stats.mean_annual, stats.cov_annual, RISK_FREE_RATE)
    stressed = portfolio_moments(weights.values, shocked_mu, shocked_cov, RISK_FREE_RATE)
    stressed_risk = compute_portfolio_risk_metrics(
        stats.log_returns,
        weights,
        RISK_FREE_RATE,
    )

    render_metric_row(
        [
            ("Base E[R]", fmt_pct(base["return"]), None, True if base["return"] > 0 else False),
            ("Stressed E[R]", fmt_pct(stressed["return"]), f"Δ {fmt_pct(stressed['return'] - base['return'])}", False if stressed["return"] < base["return"] else True),
            ("Base σ", fmt_pct(base["volatility"]), None, None),
            ("Stressed σ", fmt_pct(stressed["volatility"]), f"Δ {fmt_pct(stressed['volatility'] - base['volatility'])}", False if stressed["volatility"] > base["volatility"] else True),
            ("Stressed Sharpe", fmt_num(stressed["sharpe"]), f"Base {fmt_num(base['sharpe'])}", True if stressed["sharpe"] > 0 else False),
        ]
    )
    st.caption(
        f"Historical CVaR 95% under unshocked returns remains {fmt_pct(stressed_risk['cvar_95'])} "
        "(path-based metrics use observed returns; stressed moments are forward-looking)."
    )

    st.session_state["advisor_payload"] = {
        "advice": advice.to_dict(),
        "mapped_weights": advisor_w.to_dict(),
        "stress": {
            "equity_shock": eq_shock,
            "rates_shock": rate_shock,
            "gold_shock": gold_shock,
            "base": base,
            "stressed": stressed,
        },
    }
