"""
NSE Quant Risk Terminal — production Streamlit entry point.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import traceback
from typing import List

import streamlit as st

from config.settings import (
    ASSET_UNIVERSE,
    DEFAULT_LOOKBACK_YEARS,
    RISK_FREE_RATE,
)
from data.ingestion import fetch_price_history, validate_nse_ticker
from data.universe import display_name
from quant.returns import compute_return_statistics
from ui.components import (
    generate_mc_banner_uri,
    privacy_footer,
    render_breadcrumb,
    render_disclaimer,
    render_hero,
    render_top_nav,
)
from ui.styles import inject_global_css
from ui.theme import init_theme_state, is_dark, toggle_theme
from ui.tour import init_tour_state, render_tour, start_tour
from ui.tabs import (
    render_about_tab,
    render_ai_profiler_tab,
    render_correlation_tab,
    render_faq_tab,
    render_monte_carlo_tab,
    render_terminal_tab,
)


def _configure_page() -> None:
    st.set_page_config(
        page_title="NSE Quant Risk Terminal",
        page_icon="◈",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _render_sidebar() -> tuple[List[str], int]:
    """Universe controls, theme, tour, and privacy note. Returns tickers + lookback."""
    with st.sidebar:
        st.markdown("### Workspace Controls")

        # Theme toggle
        mode_label = "Midnight Dark" if is_dark() else "Institutional Light"
        if st.button(f"Theme: {mode_label}", use_container_width=True, key="theme_toggle"):
            toggle_theme()
            st.rerun()

        if st.button("Quick Tour", use_container_width=True, key="quick_tour"):
            start_tour()
            st.rerun()

        st.markdown("---")
        st.markdown("#### Asset Universe")

        categories = st.multiselect(
            "Categories",
            options=list(ASSET_UNIVERSE.keys()),
            default=list(ASSET_UNIVERSE.keys()),
            key="cats",
        )

        # Per-category ticker multi-selects for fine control
        selected: List[str] = []
        for cat in categories:
            opts = ASSET_UNIVERSE[cat]
            labels = {t: f"{t.replace('.NS', '')} — {display_name(t)}" for t in opts}
            picked = st.multiselect(
                cat,
                options=opts,
                default=opts,
                format_func=lambda t, m=labels: m.get(t, t),
                key=f"sel_{cat}",
            )
            selected.extend(picked)

        st.markdown("#### Custom NSE Ticker")
        custom_raw = st.text_input(
            "Add symbol (e.g. SBIN or SBIN.NS)",
            value="",
            key="custom_ticker_input",
            help="Non-existent symbols are rejected with a clear error.",
        )
        if st.button("Validate & Add", key="add_custom", use_container_width=True):
            if not custom_raw.strip():
                st.warning("Enter a ticker symbol first.")
            else:
                ok, ticker, msg = validate_nse_ticker(custom_raw)
                if ok:
                    customs = st.session_state.setdefault("custom_tickers", [])
                    if ticker not in customs:
                        customs.append(ticker)
                    st.success(msg)
                else:
                    st.error(msg)

        customs = st.session_state.get("custom_tickers", [])
        if customs:
            keep = st.multiselect(
                "Custom tickers in session",
                options=customs,
                default=customs,
                key="custom_keep",
            )
            st.session_state.custom_tickers = keep
            selected.extend(keep)

        # Deduplicate preserving order
        seen = set()
        tickers: List[str] = []
        for t in selected:
            if t not in seen:
                seen.add(t)
                tickers.append(t)

        lookback = st.slider(
            "Lookback (years)",
            min_value=1,
            max_value=10,
            value=DEFAULT_LOOKBACK_YEARS,
            key="lookback_years",
        )

        st.markdown("---")
        st.caption(f"Risk-free rate: **{RISK_FREE_RATE:.2%}**")
        st.caption("Cache TTL: 3,600s · Session-isolated")
        privacy_footer()

    return tickers, int(lookback)


def main() -> None:
    _configure_page()
    init_theme_state()
    init_tour_state()

    banner_uri = generate_mc_banner_uri()
    inject_global_css(banner_uri)

    render_hero()
    render_disclaimer()
    render_top_nav(active="Risk Terminal")
    render_breadcrumb("Home", "Risk Terminal", "Portfolio Optimizer")
    render_tour()

    tickers, lookback = _render_sidebar()

    if len(tickers) < 2:
        st.warning(
            "Select at least **two** assets to build a diversified portfolio. "
            "Use the sidebar categories or add a validated custom NSE ticker."
        )
        # Still show knowledge tabs without data dependency.
        t_faq, t_about = st.tabs(["FAQ & Knowledge Base", "About & Methodology"])
        with t_faq:
            render_faq_tab()
        with t_about:
            render_about_tab()
        return

    # ---- Data load ---------------------------------------------------------
    try:
        with st.spinner("Fetching NSE price histories (cached up to 1 hour)…"):
            prices = fetch_price_history(tuple(tickers), lookback_years=lookback)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Market data error: {exc}")
        with st.expander("Technical details"):
            st.code(traceback.format_exc())
        return

    dropped = [t for t in tickers if t not in prices.columns]
    if dropped:
        st.warning(
            "The following tickers returned no usable history and were excluded: "
            + ", ".join(dropped)
        )
    if prices.shape[1] < 2:
        st.error("Fewer than two assets have overlapping history. Adjust the universe.")
        return

    try:
        stats = compute_return_statistics(prices)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Return statistics failed: {exc}")
        return

    st.success(
        f"Loaded **{prices.shape[1]}** assets · "
        f"{prices.index.min().date()} → {prices.index.max().date()} · "
        f"{len(prices):,} trading days"
    )

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Terminal & Efficient Frontier",
            "Monte Carlo Simulation",
            "Correlation & Concentration",
            "AI Profiler & Stress Tests",
            "FAQ & Knowledge Base",
            "About & Methodology",
        ]
    )

    with tab1:
        portfolio_ctx = render_terminal_tab(stats, prices)
        st.session_state["portfolio_ctx"] = portfolio_ctx

    portfolio_ctx = st.session_state.get("portfolio_ctx", {})

    with tab2:
        render_monte_carlo_tab(portfolio_ctx)

    with tab3:
        render_correlation_tab(stats, portfolio_ctx)

    with tab4:
        render_ai_profiler_tab(stats, portfolio_ctx)

    with tab5:
        render_faq_tab()

    with tab6:
        render_about_tab()


if __name__ == "__main__":
    main()
