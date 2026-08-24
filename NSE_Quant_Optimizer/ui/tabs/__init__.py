"""Multi-tab views for the risk terminal."""

from ui.tabs.about import render_about_tab
from ui.tabs.ai_profiler import render_ai_profiler_tab
from ui.tabs.correlation import render_correlation_tab
from ui.tabs.faq import render_faq_tab
from ui.tabs.monte_carlo_tab import render_monte_carlo_tab
from ui.tabs.terminal import render_terminal_tab

__all__ = [
    "render_terminal_tab",
    "render_monte_carlo_tab",
    "render_correlation_tab",
    "render_ai_profiler_tab",
    "render_faq_tab",
    "render_about_tab",
]
