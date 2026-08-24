"""
Mean-variance optimization via scipy.optimize.minimize.

Supports Maximum Sharpe, Global Minimum Variance, Risk Parity, and
efficient-frontier generation under long-only, fully-invested constraints.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config.settings import FRONTIER_POINTS, RISK_FREE_RATE
from quant.returns import portfolio_moments


def _long_only_constraints(n: int) -> Tuple[dict, List[Tuple[float, float]]]:
    """Fully invested (weights sum to 1) and long-only bounds."""
    cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    bounds = [(0.0, 1.0)] * n
    return cons, bounds


def _safe_vol(w: np.ndarray, cov: np.ndarray) -> float:
    var = float(w @ cov @ w)
    return float(np.sqrt(max(var, 1e-18)))


def max_sharpe_portfolio(
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    risk_free: float = RISK_FREE_RATE,
) -> Dict[str, object]:
    """
    Maximize ``(E[R] - r_f) / σ`` subject to long-only, Σw = 1.
    """
    mu = mean_annual.values.astype(float)
    cov = cov_annual.values.astype(float)
    n = len(mu)
    if n == 0:
        raise ValueError("Empty asset universe.")

    cons, bounds = _long_only_constraints(n)
    w0 = np.full(n, 1.0 / n)

    def neg_sharpe(w: np.ndarray) -> float:
        ret = float(w @ mu)
        vol = _safe_vol(w, cov)
        return -((ret - risk_free) / vol)

    result = minimize(
        neg_sharpe,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    if not result.success:
        # Fall back to equal weight if optimizer struggles (rare with well-posed cov).
        weights = w0
    else:
        weights = np.clip(result.x, 0.0, 1.0)
        weights = weights / weights.sum()

    moments = portfolio_moments(weights, mean_annual, cov_annual, risk_free)
    return {
        "weights": pd.Series(weights, index=mean_annual.index, name="Max Sharpe"),
        **moments,
        "method": "Maximum Sharpe Ratio",
        "success": bool(result.success),
        "message": result.message,
    }


def min_variance_portfolio(
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    risk_free: float = RISK_FREE_RATE,
) -> Dict[str, object]:
    """Global Minimum Variance portfolio (long-only)."""
    cov = cov_annual.values.astype(float)
    n = cov.shape[0]
    cons, bounds = _long_only_constraints(n)
    w0 = np.full(n, 1.0 / n)

    def port_vol(w: np.ndarray) -> float:
        return _safe_vol(w, cov)

    result = minimize(
        port_vol,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    weights = np.clip(result.x if result.success else w0, 0.0, 1.0)
    weights = weights / weights.sum()
    moments = portfolio_moments(weights, mean_annual, cov_annual, risk_free)
    return {
        "weights": pd.Series(weights, index=mean_annual.index, name="Min Variance"),
        **moments,
        "method": "Minimum Variance",
        "success": bool(result.success),
        "message": result.message,
    }


def risk_parity_portfolio(
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    risk_free: float = RISK_FREE_RATE,
) -> Dict[str, object]:
    """
    Approximate risk-parity weights by equalizing risk contributions
    ``RC_i = w_i * (Σw)_i / σ``.
    """
    cov = cov_annual.values.astype(float)
    n = cov.shape[0]
    cons, bounds = _long_only_constraints(n)
    w0 = np.full(n, 1.0 / n)
    target = np.full(n, 1.0 / n)

    def risk_contrib_sse(w: np.ndarray) -> float:
        vol = _safe_vol(w, cov)
        mctr = cov @ w
        rc = w * mctr / vol
        # Normalize contributions to sum to 1 for stable comparison.
        rc_sum = rc.sum()
        if rc_sum <= 0:
            return 1e6
        rc_norm = rc / rc_sum
        return float(np.sum((rc_norm - target) ** 2))

    result = minimize(
        risk_contrib_sse,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 2000, "ftol": 1e-14},
    )
    weights = np.clip(result.x if result.success else w0, 0.0, 1.0)
    weights = weights / weights.sum()
    moments = portfolio_moments(weights, mean_annual, cov_annual, risk_free)
    return {
        "weights": pd.Series(weights, index=mean_annual.index, name="Risk Parity"),
        **moments,
        "method": "Risk Parity",
        "success": bool(result.success),
        "message": result.message,
    }


def efficient_frontier(
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    n_points: int = FRONTIER_POINTS,
    risk_free: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    """
    Trace the long-only efficient frontier by targeting evenly spaced returns
    between the min-variance return and the maximum individual asset return.

    Returns a DataFrame with columns: volatility, return, sharpe.
    """
    mu = mean_annual.values.astype(float)
    cov = cov_annual.values.astype(float)
    n = len(mu)
    cons_base, bounds = _long_only_constraints(n)

    # Anchor return range using GMV and highest mean asset.
    gmv = min_variance_portfolio(mean_annual, cov_annual, risk_free)
    r_min = float(gmv["return"])
    r_max = float(np.max(mu))
    if r_max <= r_min + 1e-8:
        # Degenerate case — single point frontier.
        return pd.DataFrame(
            [
                {
                    "volatility": gmv["volatility"],
                    "return": gmv["return"],
                    "sharpe": gmv["sharpe"],
                }
            ]
        )

    targets = np.linspace(r_min, r_max, n_points)
    rows: List[dict] = []
    w0 = np.full(n, 1.0 / n)

    for target in targets:
        cons = [
            cons_base,
            {"type": "eq", "fun": lambda w, t=target: float(w @ mu) - t},
        ]

        def port_vol(w: np.ndarray) -> float:
            return _safe_vol(w, cov)

        result = minimize(
            port_vol,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 800, "ftol": 1e-10},
        )
        if not result.success:
            continue
        w = np.clip(result.x, 0.0, 1.0)
        if w.sum() <= 0:
            continue
        w = w / w.sum()
        moments = portfolio_moments(w, mean_annual, cov_annual, risk_free)
        rows.append(moments)
        w0 = w  # warm-start next target

    if not rows:
        return pd.DataFrame(columns=["volatility", "return", "sharpe"])
    frontier = pd.DataFrame(rows).drop_duplicates().sort_values("volatility")
    return frontier.reset_index(drop=True)


def optimize_by_method(
    method: str,
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    risk_free: float = RISK_FREE_RATE,
) -> Dict[str, object]:
    """Dispatch helper for UI method selectors."""
    key = method.strip().lower()
    if "sharpe" in key:
        return max_sharpe_portfolio(mean_annual, cov_annual, risk_free)
    if "parity" in key:
        return risk_parity_portfolio(mean_annual, cov_annual, risk_free)
    return min_variance_portfolio(mean_annual, cov_annual, risk_free)
