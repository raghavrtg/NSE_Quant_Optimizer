"""
Historical return statistics: log returns, annualized means, covariance,
Ledoit-Wolf style shrinkage covariance, and pairwise correlations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from config.settings import TRADING_DAYS

# sklearn is commonly paired with scipy stacks; if unavailable we fall back.
try:
    from sklearn.covariance import LedoitWolf as _LW
except ImportError:  # pragma: no cover
    _LW = None


@dataclass(frozen=True)
class ReturnStatistics:
    """Container for portfolio-building moments derived from price history."""

    log_returns: pd.DataFrame
    mean_annual: pd.Series
    cov_annual: pd.DataFrame
    cov_sample_annual: pd.DataFrame
    corr: pd.DataFrame
    trading_days: int = TRADING_DAYS


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute continuously compounded daily log returns.

    ``r_t = ln(P_t / P_{t-1})``
    """
    if prices is None or prices.empty:
        raise ValueError("Price DataFrame is empty.")
    clean = prices.replace([np.inf, -np.inf], np.nan).dropna(how="any")
    if len(clean) < 2:
        raise ValueError("Need at least two price observations to compute returns.")
    log_ret = np.log(clean / clean.shift(1)).dropna(how="any")
    if log_ret.empty:
        raise ValueError("Log-return series is empty after cleaning.")
    return log_ret


def _shrinkage_covariance(log_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Annualized covariance with Ledoit-Wolf shrinkage when sklearn is present;
    otherwise a lightly regularized sample covariance (ridge toward diagonal).
    """
    X = log_returns.values
    cols = list(log_returns.columns)

    if _LW is not None:
        lw = _LW().fit(X)
        cov_daily = lw.covariance_
    else:
        sample = np.cov(X, rowvar=False, ddof=1)
        # Shrink toward diagonal variance target (simple JW-style blend).
        diag = np.diag(np.diag(sample))
        intensity = 0.2
        cov_daily = (1.0 - intensity) * sample + intensity * diag

    cov_annual = cov_daily * TRADING_DAYS
    # Numerical symmetry enforcement.
    cov_annual = 0.5 * (cov_annual + cov_annual.T)
    return pd.DataFrame(cov_annual, index=cols, columns=cols)


def compute_return_statistics(
    prices: pd.DataFrame,
    trading_days: int = TRADING_DAYS,
) -> ReturnStatistics:
    """
    Derive annualized mean returns, shrinkage covariance, sample covariance,
    and pairwise correlation from adjusted close prices.
    """
    log_returns = compute_log_returns(prices)
    mean_daily = log_returns.mean()
    mean_annual = mean_daily * trading_days

    sample_daily = log_returns.cov()
    sample_annual = sample_daily * trading_days
    sample_annual = 0.5 * (sample_annual + sample_annual.T)

    cov_annual = _shrinkage_covariance(log_returns)
    corr = log_returns.corr()

    return ReturnStatistics(
        log_returns=log_returns,
        mean_annual=mean_annual,
        cov_annual=cov_annual,
        cov_sample_annual=sample_annual,
        corr=corr,
        trading_days=trading_days,
    )


def portfolio_moments(
    weights: np.ndarray,
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    risk_free: float,
) -> dict:
    """
    Scalar portfolio return, volatility, and Sharpe for a weight vector.

    Weights are assumed to sum to 1 (long-only simplex).
    """
    w = np.asarray(weights, dtype=float).reshape(-1)
    mu = float(w @ mean_annual.values)
    var = float(w @ cov_annual.values @ w)
    vol = float(np.sqrt(max(var, 0.0)))
    sharpe = (mu - risk_free) / vol if vol > 1e-12 else 0.0
    return {"return": mu, "volatility": vol, "sharpe": sharpe}
