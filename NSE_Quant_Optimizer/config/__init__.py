"""Application configuration package."""

from config.settings import (
    RISK_FREE_RATE,
    TRADING_DAYS,
    ASSET_UNIVERSE,
    THEME_COLORS,
    DEFAULT_LOOKBACK_YEARS,
    MC_PATHS_DEFAULT,
    MC_PATHS_MIN,
    MC_PATHS_MAX,
    FRONTIER_POINTS,
)

__all__ = [
    "RISK_FREE_RATE",
    "TRADING_DAYS",
    "ASSET_UNIVERSE",
    "THEME_COLORS",
    "DEFAULT_LOOKBACK_YEARS",
    "MC_PATHS_DEFAULT",
    "MC_PATHS_MIN",
    "MC_PATHS_MAX",
    "FRONTIER_POINTS",
]
