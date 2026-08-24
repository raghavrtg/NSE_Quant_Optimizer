"""
Plotly chart builders for the NSE Quant Risk Terminal.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from quant.monte_carlo import MonteCarloResult, drawdown_distribution
from ui.theme import get_theme, style_figure


def efficient_frontier_figure(
    frontier: pd.DataFrame,
    assets_vol: pd.Series,
    assets_ret: pd.Series,
    optimal: Optional[dict] = None,
    manual: Optional[dict] = None,
) -> go.Figure:
    """Interactive efficient frontier with individual assets and portfolios."""
    c = get_theme()
    fig = go.Figure()

    if frontier is not None and not frontier.empty:
        fig.add_trace(
            go.Scatter(
                x=frontier["volatility"] * 100,
                y=frontier["return"] * 100,
                mode="lines",
                name="Efficient Frontier",
                line=dict(color=c["accent"], width=2.2),
                hovertemplate="σ=%{x:.2f}%<br>E[R]=%{y:.2f}%<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=assets_vol * 100,
            y=assets_ret * 100,
            mode="markers+text",
            name="Assets",
            text=[t.replace(".NS", "") for t in assets_ret.index],
            textposition="top center",
            textfont=dict(size=9, color=c["text_muted"]),
            marker=dict(size=9, color=c["text_muted"], symbol="diamond"),
            hovertemplate="%{text}<br>σ=%{x:.2f}%<br>E[R]=%{y:.2f}%<extra></extra>",
        )
    )

    if optimal:
        fig.add_trace(
            go.Scatter(
                x=[optimal["volatility"] * 100],
                y=[optimal["return"] * 100],
                mode="markers",
                name=optimal.get("method", "Optimal"),
                marker=dict(size=14, color=c["positive"], symbol="star"),
                hovertemplate="Optimal<br>σ=%{x:.2f}%<br>E[R]=%{y:.2f}%<extra></extra>",
            )
        )

    if manual:
        fig.add_trace(
            go.Scatter(
                x=[manual["volatility"] * 100],
                y=[manual["return"] * 100],
                mode="markers",
                name="Manual Allocation",
                marker=dict(size=12, color=c["negative"], symbol="x"),
                hovertemplate="Manual<br>σ=%{x:.2f}%<br>E[R]=%{y:.2f}%<extra></extra>",
            )
        )

    style_figure(
        fig,
        title="Efficient Frontier — Risk / Return Map",
        xaxis_title="Annualized Volatility (%)",
        yaxis_title="Annualized Expected Return (%)",
        height=460,
    )
    return fig


def weights_bar_figure(weights: pd.Series, title: str = "Portfolio Weights") -> go.Figure:
    c = get_theme()
    w = weights.sort_values(ascending=True)
    labels = [i.replace(".NS", "") for i in w.index]
    fig = go.Figure(
        go.Bar(
            x=w.values * 100,
            y=labels,
            orientation="h",
            marker=dict(color=c["accent"], line=dict(color=c["border"], width=0.5)),
            hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
        )
    )
    style_figure(fig, title=title, xaxis_title="Weight (%)", height=max(320, 28 * len(w) + 80))
    return fig


def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    c = get_theme()
    labels = [i.replace(".NS", "") for i in corr.columns]
    fig = go.Figure(
        data=go.Heatmap(
            z=corr.values,
            x=labels,
            y=labels,
            colorscale="Greys" if True else c["heatmap_scale"],
            zmin=-1,
            zmax=1,
            colorbar=dict(title="ρ"),
            hovertemplate="%{y} vs %{x}<br>ρ=%{z:.3f}<extra></extra>",
        )
    )
    style_figure(fig, title="Pairwise Return Correlation", height=520, xaxis_tickangle=-45)
    return fig


def monte_carlo_fan_chart(result: MonteCarloResult, show_sample_paths: int = 40) -> go.Figure:
    """Percentile ribbon fan chart with optional sample paths."""
    c = get_theme()
    fig = go.Figure()
    pct = result.percentiles

    # Sample paths (subtle)
    n_show = min(show_sample_paths, result.paths.shape[0])
    idx = np.linspace(0, result.paths.shape[0] - 1, n_show, dtype=int)
    for i in idx:
        fig.add_trace(
            go.Scatter(
                x=result.timeline,
                y=result.paths[i],
                mode="lines",
                line=dict(width=0.6, color=c["border"]),
                opacity=0.35,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=pct.index,
            y=pct["p95"],
            mode="lines",
            line=dict(width=0, color=c["accent"]),
            name="95th pct",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pct.index,
            y=pct["p5"],
            mode="lines",
            line=dict(width=0, color=c["accent"]),
            fill="tonexty",
            fillcolor=c["chart_fill"],
            name="5–95% Corridor",
            hovertemplate="Day %{x}<br>P5=%{y:.3f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pct.index,
            y=pct["p50"],
            mode="lines",
            name="Median (P50)",
            line=dict(color=c["accent"], width=2.4),
            hovertemplate="Day %{x}<br>P50=%{y:.3f}<extra></extra>",
        )
    )
    fig.add_hline(y=1.0, line=dict(color=c["negative"], width=1, dash="dot"), annotation_text="Initial Capital")

    style_figure(
        fig,
        title=f"Monte Carlo Wealth Paths — {result.n_paths:,} GBM Simulations",
        xaxis_title="Horizon (trading days)",
        yaxis_title="Portfolio Value (normalized)",
        height=480,
    )
    return fig


def drawdown_hist_figure(result: MonteCarloResult) -> go.Figure:
    c = get_theme()
    dd = drawdown_distribution(result.paths)
    fig = go.Figure(
        go.Histogram(
            x=dd * 100,
            nbinsx=40,
            marker=dict(color=c["accent"], line=dict(color=c["border"], width=0.5)),
            name="Max DD",
            hovertemplate="DD=%{x:.2f}%<br>Count=%{y}<extra></extra>",
        )
    )
    style_figure(
        fig,
        title="Simulated Maximum Drawdown Distribution",
        xaxis_title="Max Drawdown (%)",
        yaxis_title="Path Count",
        height=360,
    )
    return fig


def terminal_distribution_figure(result: MonteCarloResult) -> go.Figure:
    c = get_theme()
    fig = go.Figure(
        go.Histogram(
            x=result.terminal,
            nbinsx=50,
            marker=dict(color=c["text_muted"], line=dict(color=c["border"], width=0.4)),
            name="Terminal Wealth",
        )
    )
    fig.add_vline(x=1.0, line=dict(color=c["negative"], dash="dash"), annotation_text="Capital")
    fig.add_vline(x=result.median_terminal, line=dict(color=c["positive"], dash="dot"), annotation_text="Median")
    style_figure(
        fig,
        title="Terminal Wealth Distribution",
        xaxis_title="Terminal Value",
        yaxis_title="Frequency",
        height=360,
    )
    return fig


def asset_class_pie(weights: pd.Series) -> go.Figure:
    c = get_theme()
    fig = go.Figure(
        go.Pie(
            labels=list(weights.index),
            values=list(weights.values),
            hole=0.55,
            marker=dict(colors=[c["accent"], c["text_muted"], c["card_alt"], c["border"]], line=dict(color=c["bg"], width=2)),
            textinfo="label+percent",
            hovertemplate="%{label}: %{percent}<extra></extra>",
        )
    )
    style_figure(fig, title="Advisor Asset-Class Mix", height=380, showlegend=False)
    return fig


def covariance_table_figure(cov: pd.DataFrame) -> go.Figure:
    """Heat-style table for annualized covariance (scaled ×100² for readability)."""
    c = get_theme()
    scaled = cov * 10_000  # variance in percent-squared terms approx
    labels = [i.replace(".NS", "") for i in cov.columns]
    fig = go.Figure(
        data=go.Heatmap(
            z=scaled.values,
            x=labels,
            y=labels,
            colorscale="Greys",
            colorbar=dict(title="Cov ×10⁴"),
            hovertemplate="%{y}, %{x}<br>%{z:.3f}<extra></extra>",
        )
    )
    style_figure(fig, title="Annualized Covariance (×10⁴)", height=520, xaxis_tickangle=-45)
    return fig
