"""
Reusable UI components: hero, disclaimer, breadcrumbs, metric cards, banners.
"""

from __future__ import annotations

import base64
import io
from typing import Optional

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFilter

from config.settings import APP_SUBTITLE, APP_TITLE, DISCLAIMER_TEXT
from ui.theme import get_theme


@st.cache_data(show_spinner=False)
def generate_mc_banner_uri(width: int = 1400, height: int = 280, seed: int = 7) -> str:
    """
    Synthesize a subtle monochrome Monte Carlo fan-chart banner as a data URI.
    Cached so the PNG is generated once per session process.
    """
    rng = np.random.default_rng(seed)
    img = Image.new("RGB", (width, height), (18, 20, 26))
    draw = ImageDraw.Draw(img, "RGBA")

    n_paths = 48
    steps = 120
    x = np.linspace(40, width - 40, steps)

    for i in range(n_paths):
        mu = rng.normal(0.0005, 0.0008)
        sigma = rng.uniform(0.008, 0.025)
        z = rng.standard_normal(steps)
        log_path = np.cumsum(mu - 0.5 * sigma**2 + sigma * z)
        y_norm = (log_path - log_path.min()) / ((log_path.max() - log_path.min()) + 1e-9)
        y = height * (0.75 - 0.55 * y_norm)
        alpha = int(28 + 40 * (i / n_paths))
        pts = list(zip(x.tolist(), y.tolist()))
        draw.line(pts, fill=(200, 205, 212, alpha), width=1)

    # Soft percentile ribbon
    mid = height * 0.45
    for amp, a in ((55, 35), (90, 22), (130, 14)):
        upper = [(float(xi), mid - amp * np.sin(k / 18)) for k, xi in enumerate(x)]
        lower = [(float(xi), mid + amp * np.sin(k / 18 + 0.4)) for k, xi in enumerate(x)]
        poly = upper + list(reversed(lower))
        draw.polygon(poly, fill=(160, 165, 175, a))

    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def render_hero() -> None:
    """Top hero band with Monte Carlo banner and product title."""
    st.markdown(
        f"""
        <div class="nse-hero">
          <div class="nse-hero-inner">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer() -> None:
    st.markdown(
        f'<div class="nse-disclaimer">{DISCLAIMER_TEXT}</div>',
        unsafe_allow_html=True,
    )


def render_breadcrumb(*parts: str) -> None:
    if not parts:
        return
    crumbs = []
    for i, p in enumerate(parts):
        if i == len(parts) - 1:
            crumbs.append(f'<span class="current">{p}</span>')
        else:
            crumbs.append(f"<span>{p}</span>")
    joined = '<span class="sep">›</span>'.join(crumbs)
    st.markdown(f'<div class="nse-breadcrumb">{joined}</div>', unsafe_allow_html=True)


def render_top_nav(active: str = "Risk Terminal") -> None:
    items = ["Home", "Risk Terminal", "Portfolio Optimizer", "Knowledge Base"]
    html = ['<div class="nse-nav">']
    for it in items:
        cls = "nse-nav-item active" if it == active else "nse-nav-item"
        html.append(f'<span class="{cls}">{it}</span>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def metric_card_html(title: str, value: str, delta: Optional[str] = None, positive: Optional[bool] = None) -> str:
    c = get_theme()
    delta_html = ""
    if delta is not None:
        cls = "nse-delta-pos" if positive else ("nse-delta-neg" if positive is False else "")
        color = c["text_muted"] if positive is None else ""
        style = f' style="color:{color}"' if positive is None else ""
        delta_html = f'<div class="{cls}"{style}>{delta}</div>'
    return (
        f'<div class="nse-card"><h4>{title}</h4>'
        f'<div class="nse-metric-value">{value}</div>{delta_html}</div>'
    )


def render_metric_row(cards: list[tuple]) -> None:
    """
    Render a row of metric cards.

    Each card is ``(title, value, delta_or_None, positive_or_None)``.
    """
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        title, value, delta, positive = card if len(card) == 4 else (*card, None, None)
        with col:
            st.markdown(metric_card_html(title, value, delta, positive), unsafe_allow_html=True)


def privacy_footer() -> None:
    st.markdown(
        """
        <div class="nse-privacy">
          <strong>Data Privacy:</strong> All inputs, custom weights, and simulation
          results execute strictly in your isolated browser session (Streamlit
          session state). No portfolio data is written to shared storage; there is
          zero cross-user visibility.
        </div>
        """,
        unsafe_allow_html=True,
    )


def fmt_pct(x: float, digits: int = 2) -> str:
    return f"{100.0 * x:.{digits}f}%"


def fmt_num(x: float, digits: int = 2) -> str:
    if x == float("inf"):
        return "∞"
    return f"{x:.{digits}f}"
