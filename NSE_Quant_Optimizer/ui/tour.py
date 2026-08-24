"""
First-time user onboarding tour — session-state step tracker with Skip / Quick Tour.
"""

from __future__ import annotations

from typing import List, Tuple

import streamlit as st

TOUR_STEPS: List[Tuple[str, str]] = [
    (
        "Welcome to the NSE Quant Risk Terminal",
        "This institutional workspace helps you construct, optimize, and stress-test "
        "portfolios across NSE equities, ETFs, REITs, G-Secs, and commodity indices. "
        "All analytics run locally in your isolated session.",
    ),
    (
        "Build Your Universe",
        "Use the sidebar to select asset categories, add custom NSE tickers "
        "(with .NS handled automatically), and set lookback history. Prices are cached "
        "for one hour via yfinance.",
    ),
    (
        "Optimize & Inspect Risk",
        "Tab 1 runs Max Sharpe, Min Variance, or Risk Parity optimization and plots "
        "the efficient frontier. Risk cards show VaR, CVaR, Sortino, and drawdown.",
    ),
    (
        "Simulate Forward Paths",
        "Tab 2 launches a vectorized Geometric Brownian Motion engine (5k–10k paths) "
        "so you can inspect percentile corridors and capital-erosion probability.",
    ),
    (
        "Profile & Stress-Test",
        "Tab 4’s AI Profiler maps age, horizon, risk tolerance, and objective into a "
        "lifecycle allocation. Apply custom scenario shocks before exporting tear-sheets.",
    ),
]


def init_tour_state() -> None:
    if "tour_completed" not in st.session_state:
        st.session_state.tour_completed = False
    if "tour_step" not in st.session_state:
        st.session_state.tour_step = 0
    if "tour_active" not in st.session_state:
        # Auto-launch for first-time visitors.
        st.session_state.tour_active = not st.session_state.tour_completed


def start_tour() -> None:
    init_tour_state()
    st.session_state.tour_active = True
    st.session_state.tour_step = 0


def skip_tour() -> None:
    st.session_state.tour_active = False
    st.session_state.tour_completed = True
    st.session_state.tour_step = 0


def _advance() -> None:
    step = st.session_state.tour_step + 1
    if step >= len(TOUR_STEPS):
        skip_tour()
    else:
        st.session_state.tour_step = step


def render_tour() -> None:
    """Render the guided walkthrough panel when active."""
    init_tour_state()
    if not st.session_state.tour_active:
        return

    step = int(st.session_state.tour_step)
    step = max(0, min(step, len(TOUR_STEPS) - 1))
    title, body = TOUR_STEPS[step]
    progress = (step + 1) / len(TOUR_STEPS) * 100

    st.markdown(
        f"""
        <div class="nse-tour-panel nse-fade">
          <div class="nse-tour-step">GUIDED TOUR · STEP {step + 1} / {len(TOUR_STEPS)}</div>
          <div class="nse-progress"><div style="width:{progress:.0f}%"></div></div>
          <div class="nse-tour-title">{title}</div>
          <div class="nse-tour-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("Skip Tour", key="tour_skip", use_container_width=True):
            skip_tour()
            st.rerun()
    with c2:
        label = "Finish" if step == len(TOUR_STEPS) - 1 else "Next"
        if st.button(label, key="tour_next", use_container_width=True, type="primary"):
            _advance()
            st.rerun()
