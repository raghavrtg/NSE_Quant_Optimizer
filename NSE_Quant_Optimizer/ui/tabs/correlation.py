"""
Tab 3 — Correlation & Concentration Risk.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
import streamlit as st

from quant.returns import ReturnStatistics
from ui.charts import correlation_heatmap, covariance_table_figure
from ui.components import fmt_pct, render_metric_row


def render_correlation_tab(
    stats: ReturnStatistics,
    portfolio_ctx: Dict[str, Any],
) -> None:
    st.subheader("Correlation & Concentration Risk")
    st.caption(
        "Pairwise return correlations, shrinkage covariance, and Herfindahl-based "
        "concentration diagnostics for the active sleeve."
    )

    st.plotly_chart(correlation_heatmap(stats.corr), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(covariance_table_figure(stats.cov_annual), use_container_width=True)
    with c2:
        st.markdown("##### Covariance Matrix (Annualized)")
        display = stats.cov_annual.copy()
        display.index = [i.replace(".NS", "") for i in display.index]
        display.columns = [c.replace(".NS", "") for c in display.columns]
        st.dataframe(display.style.format("{:.6f}"), use_container_width=True, height=480)

    if portfolio_ctx and "manual_weights" in portfolio_ctx:
        w: pd.Series = portfolio_ctx["manual_weights"]
        hhi = float(np.sum(np.square(w.values)))
        effective_n = 1.0 / hhi if hhi > 0 else 0.0
        top = w.sort_values(ascending=False).head(3)
        top_share = float(top.sum())
        avg_corr = float(
            stats.corr.values[np.triu_indices_from(stats.corr.values, k=1)].mean()
        ) if stats.corr.shape[0] > 1 else 0.0

        render_metric_row(
            [
                ("HHI Concentration", f"{hhi:.3f}", "Σ w² (1/N = equal)", None),
                ("Effective N", f"{effective_n:.2f}", "1 / HHI", True if effective_n >= 3 else False),
                ("Top-3 Weight", fmt_pct(top_share), ", ".join(t.replace(".NS", "") for t in top.index), False if top_share > 0.6 else True),
                ("Avg Pairwise ρ", f"{avg_corr:.3f}", "Upper triangle mean", False if avg_corr > 0.7 else True),
            ]
        )

        st.markdown("##### Correlation Matrix")
        corr_disp = stats.corr.copy()
        corr_disp.index = [i.replace(".NS", "") for i in corr_disp.index]
        corr_disp.columns = [c.replace(".NS", "") for c in corr_disp.columns]
       try:
    st.dataframe(corr_disp.style.format("{:.3f}").background_gradient(cmap="Greys"), use_container_width=True)
except Exception:
    st.dataframe(corr_disp.round(3), use_container_width=True)
    else:
        st.info("Manual weights from Tab 1 unlock concentration diagnostics.")
