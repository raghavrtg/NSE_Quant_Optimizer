"""
Pairwise correlation matrix and concentration risk visualization tab.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_correlation_tab(stats, portfolio_ctx: dict) -> None:
    st.markdown("### Asset Correlation & Concentration Dynamics")
    st.markdown(
        "Low or negative cross-asset correlation is the mathematical foundation of diversification. "
        "High correlation clusters indicate concentration risk."
    )

    # Safely retrieve correlation matrix whether stats is an object or dictionary
    if hasattr(stats, "correlation_matrix"):
        corr_df = stats.correlation_matrix
    elif isinstance(stats, dict):
        corr_df = stats.get("correlation_matrix")
    else:
        corr_df = None

    if corr_df is None or (isinstance(corr_df, pd.DataFrame) and corr_df.empty):
        st.info("Insufficient return history to compute correlation matrix.")
        return

    # 1. Interactive Heatmap
    fig_corr = px.imshow(
        corr_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1.0,
        zmax=1.0,
        title="Pairwise Asset Log-Return Correlation Matrix",
    )
    fig_corr.update_layout(
        height=550,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    # 2. Raw Correlation Matrix Table
    st.markdown("#### Correlation Matrix Table")
    try:
        st.dataframe(
            corr_df.style.format("{:.3f}").background_gradient(cmap="Greys"),
            use_container_width=True,
        )
    except Exception:
        st.dataframe(corr_df.round(3), use_container_width=True)
