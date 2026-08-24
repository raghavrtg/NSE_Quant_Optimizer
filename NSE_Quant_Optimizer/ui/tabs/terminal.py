"""
Tab 1 — Terminal & Efficient Frontier.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
import streamlit as st

from config.settings import RISK_FREE_RATE
from quant.optimization import efficient_frontier, optimize_by_method
from quant.returns import ReturnStatistics, portfolio_moments
from quant.risk_metrics import compute_portfolio_risk_metrics
from ui.charts import efficient_frontier_figure, weights_bar_figure
from ui.components import fmt_num, fmt_pct, render_metric_row
from utils import build_tearsheet_payload, tearsheet_to_csv, tearsheet_to_json


def render_terminal_tab(
    stats: ReturnStatistics,
    prices: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Render optimizer controls, frontier chart, weight bars, risk cards,
    and manual allocation sliders. Returns the active portfolio context
    for downstream tabs / exports.
    """
    st.subheader("Portfolio Optimizer")
    st.caption(
        f"Risk-free rate = {RISK_FREE_RATE:.2%} (RBI repo / G-Sec benchmark context). "
        "Long-only, fully invested constraints."
    )

    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        method = st.selectbox(
            "Optimization Method",
            [
                "Maximum Sharpe Ratio",
                "Minimum Variance",
                "Risk Parity",
            ],
            index=0,
            key="opt_method",
        )
    with c2:
        st.metric("Assets in Universe", len(stats.mean_annual))
    with c3:
        st.metric("History (trading days)", len(stats.log_returns))

    with st.spinner("Solving portfolio optimization…"):
        optimal = optimize_by_method(
            method,
            stats.mean_annual,
            stats.cov_annual,
            RISK_FREE_RATE,
        )
        frontier = efficient_frontier(
            stats.mean_annual,
            stats.cov_annual,
            risk_free=RISK_FREE_RATE,
        )

    opt_weights: pd.Series = optimal["weights"]  # type: ignore[assignment]

    # --- Manual allocation sliders (no re-download) -------------------------
    st.markdown("##### Manual Allocation Overlay")
    st.caption(
        "Adjust weights in real time. Metrics recalculate from cached returns — "
        "price history is not re-downloaded."
    )

    if "manual_weights" not in st.session_state or set(st.session_state.manual_weights.index) != set(opt_weights.index):
        st.session_state.manual_weights = opt_weights.copy()

    if st.button("Reset Sliders to Optimal", key="reset_sliders"):
        st.session_state.manual_weights = opt_weights.copy()
        for t, v in opt_weights.items():
            st.session_state[f"w_{t}"] = float(v) * 100.0
        st.rerun()

    slider_cols = st.columns(min(4, len(opt_weights)))
    new_weights = {}
    for i, ticker in enumerate(opt_weights.index):
        col = slider_cols[i % len(slider_cols)]
        with col:
            key = f"w_{ticker}"
            default_frac = float(st.session_state.manual_weights.get(ticker, opt_weights[ticker]))
            if key not in st.session_state:
                st.session_state[key] = float(np.clip(default_frac * 100.0, 0.0, 100.0))
            new_weights[ticker] = st.slider(
                ticker.replace(".NS", ""),
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                key=key,
                format="%.0f%%",
                help="Percent of portfolio. Weights are renormalized to sum to 100%.",
            )

    raw = pd.Series(new_weights, dtype=float) / 100.0
    if raw.sum() <= 1e-12:
        st.warning("All manual weights are zero — falling back to equal weight.")
        manual_weights = pd.Series(1.0 / len(raw), index=raw.index)
    else:
        manual_weights = raw / raw.sum()
    st.session_state.manual_weights = manual_weights

    # Moments for optimal + manual
    asset_vol = pd.Series(
        {t: float(stats.cov_annual.loc[t, t] ** 0.5) for t in stats.mean_annual.index}
    )
    manual_moments = portfolio_moments(
        manual_weights.values,
        stats.mean_annual,
        stats.cov_annual,
        RISK_FREE_RATE,
    )
    risk = compute_portfolio_risk_metrics(stats.log_returns, manual_weights, RISK_FREE_RATE)

    render_metric_row(
        [
            ("Expected Return", fmt_pct(manual_moments["return"]), "Annualized", True if manual_moments["return"] > 0 else False),
            ("Volatility", fmt_pct(manual_moments["volatility"]), "Annualized σ", None),
            ("Sharpe Ratio", fmt_num(manual_moments["sharpe"]), f"rf={RISK_FREE_RATE:.2%}", True if manual_moments["sharpe"] > 0 else False),
            ("Max Drawdown", fmt_pct(risk["max_drawdown"]), "Historical path", False),
        ]
    )
    render_metric_row(
        [
            ("Param VaR 95% 1d", fmt_pct(risk["parametric_var_95_1d"]), None, False),
            ("Param VaR 99% 30d", fmt_pct(risk["parametric_var_99_30d"]), None, False),
            ("Hist VaR 95% 1d", fmt_pct(risk["historical_var_95_1d"]), None, False),
            ("CVaR 95%", fmt_pct(risk["cvar_95"]), "Expected Shortfall", False),
            ("Sortino", fmt_num(risk["sortino"]), None, True if risk["sortino"] > 0 else False),
        ]
    )

    fig = efficient_frontier_figure(
        frontier,
        asset_vol,
        stats.mean_annual,
        optimal={
            "volatility": optimal["volatility"],
            "return": optimal["return"],
            "method": optimal["method"],
        },
        manual=manual_moments,
    )
    st.plotly_chart(fig, use_container_width=True)

    w1, w2 = st.columns(2)
    with w1:
        st.plotly_chart(weights_bar_figure(opt_weights, "Optimal Weights"), use_container_width=True)
    with w2:
        st.plotly_chart(weights_bar_figure(manual_weights, "Manual Weights (Normalized)"), use_container_width=True)

    # Export
    payload = build_tearsheet_payload(
        weights=manual_weights,
        metrics={**risk, **manual_moments},
        method=str(optimal["method"]),
        tickers_meta={
            "tickers": list(manual_weights.index),
            "price_start": str(prices.index.min().date()),
            "price_end": str(prices.index.max().date()),
            "n_obs": int(len(prices)),
        },
        extra={
            "optimal_weights": opt_weights.to_dict(),
            "optimizer_success": optimal.get("success"),
        },
    )
    j1, j2 = st.columns(2)
    with j1:
        st.download_button(
            "Download Tear-Sheet (JSON)",
            data=tearsheet_to_json(payload),
            file_name="nse_portfolio_tearsheet.json",
            mime="application/json",
            use_container_width=True,
        )
    with j2:
        st.download_button(
            "Download Tear-Sheet (CSV)",
            data=tearsheet_to_csv(payload),
            file_name="nse_portfolio_tearsheet.csv",
            mime="text/csv",
            use_container_width=True,
        )

    return {
        "optimal": optimal,
        "manual_weights": manual_weights,
        "manual_moments": manual_moments,
        "risk": risk,
        "frontier": frontier,
        "tearsheet": payload,
    }
