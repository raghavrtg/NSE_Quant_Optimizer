"""
Vectorized Geometric Brownian Motion Monte Carlo engine.

Simulates portfolio terminal wealth over a user-selected horizon and reports
percentile corridors plus probability of capital erosion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import TRADING_DAYS


@dataclass(frozen=True)
class MonteCarloResult:
    """Structured Monte Carlo output for charting and tear-sheets."""

    paths: np.ndarray  # shape (n_paths, n_steps + 1)
    timeline: np.ndarray  # day indices 0..horizon
    percentiles: pd.DataFrame  # columns p5, p50, p95 indexed by day
    terminal: np.ndarray
    prob_capital_erosion: float
    expected_terminal: float
    median_terminal: float
    horizon_days: int
    n_paths: int
    mu_annual: float
    sigma_annual: float


def run_gbm_simulation(
    mu_annual: float,
    sigma_annual: float,
    horizon_days: int,
    n_paths: int = 7_500,
    initial_value: float = 1.0,
    seed: Optional[int] = 42,
    trading_days: int = TRADING_DAYS,
) -> MonteCarloResult:
    """
    Simulate GBM paths:

        S_{t+1} = S_t · exp((μ − ½σ²)Δt + σ√Δt · Z),  Z ~ N(0,1)

    Parameters are annualized; Δt = 1 / trading_days.
    """
    if horizon_days < 1:
        raise ValueError("horizon_days must be >= 1.")
    if n_paths < 100:
        raise ValueError("n_paths must be >= 100.")
    if sigma_annual < 0:
        raise ValueError("sigma_annual must be non-negative.")
    if initial_value <= 0:
        raise ValueError("initial_value must be positive.")

    rng = np.random.default_rng(seed)
    dt = 1.0 / float(trading_days)
    drift = (mu_annual - 0.5 * sigma_annual**2) * dt
    diffusion = sigma_annual * np.sqrt(dt)

    # Vectorized shocks: (n_paths, horizon)
    z = rng.standard_normal(size=(n_paths, horizon_days))
    log_increments = drift + diffusion * z
    log_paths = np.cumsum(log_increments, axis=1)
    # Prepend zeros so column 0 is the starting value.
    log_paths = np.concatenate([np.zeros((n_paths, 1)), log_paths], axis=1)
    paths = initial_value * np.exp(log_paths)

    timeline = np.arange(0, horizon_days + 1)
    p5 = np.percentile(paths, 5, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p95 = np.percentile(paths, 95, axis=0)
    percentiles = pd.DataFrame(
        {"day": timeline, "p5": p5, "p50": p50, "p95": p95}
    ).set_index("day")

    terminal = paths[:, -1]
    prob_erosion = float(np.mean(terminal < initial_value))

    return MonteCarloResult(
        paths=paths,
        timeline=timeline,
        percentiles=percentiles,
        terminal=terminal,
        prob_capital_erosion=prob_erosion,
        expected_terminal=float(terminal.mean()),
        median_terminal=float(np.median(terminal)),
        horizon_days=horizon_days,
        n_paths=n_paths,
        mu_annual=mu_annual,
        sigma_annual=sigma_annual,
    )


def drawdown_distribution(paths: np.ndarray) -> np.ndarray:
    """
    Per-path maximum drawdown (positive fractions) across the simulated horizon.
    """
    if paths.ndim != 2:
        raise ValueError("paths must be 2-D (n_paths, n_steps).")
    peak = np.maximum.accumulate(paths, axis=1)
    dd = (paths - peak) / np.where(peak == 0, 1.0, peak)
    return np.abs(dd.min(axis=1))
