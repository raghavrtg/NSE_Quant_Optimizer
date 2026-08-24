"""
Institutional CSS injection for Streamlit — dark/light themes, micro-animations,
disclaimer banner, metric cards, and navigation chrome.
"""

from __future__ import annotations

import streamlit as st

from ui.theme import get_theme, is_dark


def inject_global_css(banner_data_uri: str | None = None) -> None:
    """Inject theme-aware CSS into the Streamlit document head."""
    c = get_theme()
    dark = is_dark()
    banner_bg = (
        f"url('{banner_data_uri}')" if banner_data_uri else "linear-gradient(120deg, #1a1d24 0%, #2c3038 50%, #1a1d24 100%)"
    )

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif;
    }}

    .stApp {{
        background-color: {c['bg']};
        color: {c['text']};
    }}

    /* Hide default Streamlit chrome noise */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    /* Subtle fade-in for main blocks */
    @keyframes nseFadeUp {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes nsePulseBorder {{
        0%, 100% {{ border-color: {c['border']}; }}
        50% {{ border-color: {c['accent']}; }}
    }}

    .nse-fade {{
        animation: nseFadeUp 0.45s ease-out both;
    }}

    .nse-hero {{
        position: relative;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 1.1rem;
        border: 1px solid {c['border']};
        background-image: {banner_bg};
        background-size: cover;
        background-position: center;
        min-height: 148px;
        animation: nseFadeUp 0.55s ease-out both;
    }}
    .nse-hero::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: {c['banner_overlay']};
        backdrop-filter: blur(3px);
        -webkit-backdrop-filter: blur(3px);
    }}
    .nse-hero-inner {{
        position: relative;
        z-index: 1;
        padding: 1.6rem 1.75rem;
    }}
    .nse-hero h1 {{
        margin: 0 0 0.35rem 0;
        font-size: 1.65rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        color: {c['text']};
    }}
    .nse-hero p {{
        margin: 0;
        color: {c['text_muted']};
        font-size: 0.95rem;
        font-weight: 400;
    }}

    .nse-disclaimer {{
        background: {c['card']};
        border: 1px solid {c['border']};
        border-left: 3px solid {c['accent']};
        padding: 0.85rem 1rem;
        border-radius: 2px;
        font-size: 0.78rem;
        line-height: 1.45;
        color: {c['text_muted']};
        margin-bottom: 1rem;
        animation: nseFadeUp 0.5s ease-out 0.05s both;
    }}

    .nse-breadcrumb {{
        font-size: 0.78rem;
        color: {c['text_muted']};
        margin-bottom: 0.75rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-family: 'IBM Plex Mono', monospace;
    }}
    .nse-breadcrumb span.sep {{
        margin: 0 0.4rem;
        opacity: 0.5;
    }}
    .nse-breadcrumb span.current {{
        color: {c['text']};
        font-weight: 500;
    }}

    .nse-nav {{
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid {c['border']};
    }}
    .nse-nav-item {{
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: {c['text_muted']};
        padding: 0.35rem 0.65rem;
        border: 1px solid transparent;
        border-radius: 2px;
    }}
    .nse-nav-item.active {{
        color: {c['text']};
        border-color: {c['border']};
        background: {c['card']};
    }}

    .nse-card {{
        background: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
        animation: nseFadeUp 0.4s ease-out both;
        transition: border-color 0.25s ease, transform 0.25s ease;
    }}
    .nse-card:hover {{
        border-color: {c['accent']};
        transform: translateY(-1px);
    }}
    .nse-card h4 {{
        margin: 0 0 0.35rem 0;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {c['text_muted']};
        font-weight: 500;
    }}
    .nse-metric-value {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.35rem;
        font-weight: 500;
        color: {c['text']};
        line-height: 1.2;
    }}
    .nse-delta-pos {{ color: {c['positive']}; font-size: 0.8rem; }}
    .nse-delta-neg {{ color: {c['negative']}; font-size: 0.8rem; }}

    .nse-tour-panel {{
        background: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 1.25rem;
        animation: nsePulseBorder 2.8s ease-in-out infinite;
    }}
    .nse-tour-step {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: {c['text_muted']};
        margin-bottom: 0.5rem;
    }}
    .nse-tour-title {{
        font-size: 1.1rem;
        font-weight: 600;
        color: {c['text']};
        margin-bottom: 0.4rem;
    }}
    .nse-tour-body {{
        font-size: 0.9rem;
        color: {c['text_muted']};
        line-height: 1.5;
        margin-bottom: 1rem;
    }}
    .nse-progress {{
        height: 3px;
        background: {c['border']};
        border-radius: 2px;
        margin-bottom: 1rem;
        overflow: hidden;
    }}
    .nse-progress > div {{
        height: 100%;
        background: {c['accent']};
        transition: width 0.35s ease;
    }}

    .nse-privacy {{
        font-size: 0.72rem;
        color: {c['text_muted']};
        border-top: 1px solid {c['border']};
        padding-top: 0.75rem;
        margin-top: 1rem;
    }}

    /* Streamlit widget restyle */
    section[data-testid="stSidebar"] {{
        background-color: {c['card']};
        border-right: 1px solid {c['border']};
    }}
    section[data-testid="stSidebar"] * {{
        color: {c['text']};
    }}
    div[data-testid="stMetric"] {{
        background: {c['card']};
        border: 1px solid {c['border']};
        border-radius: 3px;
        padding: 0.65rem 0.85rem;
    }}
    div[data-testid="stTabs"] button[role="tab"] {{
        font-family: 'IBM Plex Sans', sans-serif;
        letter-spacing: 0.03em;
        color: {c['text_muted']};
    }}
    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: {c['text']};
        border-bottom-color: {c['accent']} !important;
    }}
    .stDownloadButton button, .stButton > button {{
        border-radius: 2px !important;
        border: 1px solid {c['border']} !important;
        background: {c['card_alt']} !important;
        color: {c['text']} !important;
        transition: border-color 0.2s ease, background 0.2s ease !important;
    }}
    .stDownloadButton button:hover, .stButton > button:hover {{
        border-color: {c['accent']} !important;
    }}
    hr {{
        border-color: {c['border']} !important;
    }}
    {'/* dark scrollbar */' if dark else ''}
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-thumb {{ background: {c['border']}; border-radius: 4px; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
