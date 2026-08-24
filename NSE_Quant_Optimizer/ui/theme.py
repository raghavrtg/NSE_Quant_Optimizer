"""
Theme tokens and Plotly layout helpers for institutional Dark / Light modes.
"""

from __future__ import annotations

from typing import Dict

import plotly.graph_objects as go
import streamlit as st

from config.settings import THEME_COLORS


def init_theme_state() -> None:
    """Ensure session-state theme key exists (default: dark)."""
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"


def get_theme() -> Dict[str, str]:
    """Active theme color dictionary."""
    init_theme_state()
    mode = st.session_state.get("theme_mode", "dark")
    return THEME_COLORS.get(mode, THEME_COLORS["dark"])


def is_dark() -> bool:
    init_theme_state()
    return st.session_state.get("theme_mode", "dark") == "dark"


def toggle_theme() -> None:
    init_theme_state()
    st.session_state.theme_mode = "light" if is_dark() else "dark"


def plotly_layout(**overrides) -> dict:
    """Base Plotly layout matching the active institutional theme."""
    c = get_theme()
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", color=c["text"], size=12),
        margin=dict(l=48, r=24, t=48, b=48),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=c["border"], orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(
            gridcolor=c["border"],
            zerolinecolor=c["border"],
            linecolor=c["border"],
            tickfont=dict(color=c["text_muted"]),
            title_font=dict(color=c["text_muted"]),
        ),
        yaxis=dict(
            gridcolor=c["border"],
            zerolinecolor=c["border"],
            linecolor=c["border"],
            tickfont=dict(color=c["text_muted"]),
            title_font=dict(color=c["text_muted"]),
        ),
        colorway=[c["accent"], c["text_muted"], c["positive"], c["negative"], c["chart_line"]],
        hovermode="x unified",
    )
    layout.update(overrides)
    return layout


def style_figure(fig: go.Figure, **overrides) -> go.Figure:
    """Apply theme layout to an existing figure."""
    fig.update_layout(**plotly_layout(**overrides))
    return fig
