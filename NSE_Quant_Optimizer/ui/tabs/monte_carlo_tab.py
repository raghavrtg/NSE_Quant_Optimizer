"""
Tab 2 — Monte Carlo Simulation.
"""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from config.settings import (
    MC_HORIZON_DEFAULT,
    MC_HORIZON_MAX,
    MC_HORIZON_MIN,
    MC_PATHS_DEFAULT,
    MC_PATHS_MAX,
    MC_PATHS_MIN,
)
from quant.monte_carlo import run_gbm_simulation
from ui.charts import drawdown_hist_figure, monte_carlo_fan_chart, terminal_distribution_figure
from ui.components import fmt_pct, render_metric_row


def render_monte_carlo_tab(portfolio_ctx: Dict[str, Any]) -> None:
    """GBM fan chart, terminal distribution, and drawdown histogram."""
    st.subheader("Monte Carlo Engine")
    st.caption(
        "Vectorized Geometric Brownian Motion using portfolio annualized drift and "
        "volatility from the active manual allocation."
    )

    if not portfolio_ctx:
        st.info("Construct a portfolio in Tab 1 to unlock Monte Carlo simulation.")
        return

    moments = portfolio_ctx["manual_moments"]
    mu = float(moments["return"])
    sigma = float(moments["volatility"])

    c1, c2, c3 = st.columns(3)
    with c1:
        horizon = st.slider(
            "Forecast Horizon (days)",
            min_value=MC_HORIZON_MIN,
            max_value=MC_HORIZON_MAX,
            value=MC_HORIZON_DEFAULT,
            step=1,
            key="mc_horizon",
        )
    with c2:
        n_paths = st.slider(
            "Simulation Paths",
            min_value=MC_PATHS_MIN,
            max_value=MC_PATHS_MAX,
            value=MC_PATHS_DEFAULT,
            step=500,
            key="mc_paths",
        )
    with c3:
        seed = st.number_input("Random Seed", min_value=0, max_value=999_999, value=42, step=1, key="mc_seed")

    with st.spinner(f"Simulating {n_paths:,} GBM paths…"):
        result = run_gbm_simulation(
            mu_annual=mu,
            sigma_annual=sigma,
            horizon_days=int(horizon),
            n_paths=int(n_paths),
            initial_value=1.0,
            seed=int(seed),
        )

    erosion = result.prob_capital_erosion
    render_metric_row(
        [
            ("P5 Terminal", f"{result.percentiles['p5'].iloc[-1]:.3f}", "5th percentile", None),
            ("P50 Terminal", f"{result.median_terminal:.3f}", "Median outcome", True if result.median_terminal >= 1 else False),
            ("P95 Terminal", f"{result.percentiles['p95'].iloc[-1]:.3f}", "95th percentile", True),
            (
                "P(Capital Erosion)",
                fmt_pct(erosion),
                "Terminal < 1.0",
                False if erosion > 0.25 else True,
            ),
        ]
    )

    st.plotly_chart(monte_carlo_fan_chart(result), use_container_width=True)
    d1, d2 = st.columns(2)
    with d1:
        st.plotly_chart(terminal_distribution_figure(result), use_container_width=True)
    with d2:
        st.plotly_chart(drawdown_hist_figure(result), use_container_width=True)

    st.session_state["mc_result_summary"] = {
        "horizon_days": result.horizon_days,
        "n_paths": result.n_paths,
        "mu_annual": result.mu_annual,
        "sigma_annual": result.sigma_annual,
        "prob_capital_erosion": result.prob_capital_erosion,
        "expected_terminal": result.expected_terminal,
        "median_terminal": result.median_terminal,
        "p5": float(result.percentiles["p5"].iloc[-1]),
        "p95": float(result.percentiles["p95"].iloc[-1]),
    }
