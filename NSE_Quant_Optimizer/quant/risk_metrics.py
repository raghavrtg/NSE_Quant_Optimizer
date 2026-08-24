"""
Portfolio risk metrics: parametric VaR, historical VaR, CVaR, Max DD, Sortino.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from scipy import stats

from config.settings import RISK_FREE_RATE, TRADING_DAYS


def _portfolio_daily_returns(
    log_returns: pd.DataFrame,
    weights: pd.Series,
) -> pd.Series:
    """Aligned weighted portfolio log returns (daily)."""
    w = weights.reindex(log_returns.columns).fillna(0.0).values
    if not np.isclose(w.sum(), 1.0, atol=1e-6) and w.sum() > 0:
        w = w / w.sum()
    port = log_returns.values @ w
    return pd.Series(port, index=log_returns.index, name="portfolio")


def parametric_var(
    mu_daily: float,
    sigma_daily: float,
    confidence: float,
    horizon_days: int,
) -> float:
    """
    Parametric (Gaussian) VaR as a positive loss fraction of portfolio value.

    Uses the mean-adjusted normal quantile over ``horizon_days``.
    """
    z = stats.norm.ppf(1.0 - confidence)
    # Horizon scaling under i.i.d. log-return assumption.
    mu_h = mu_daily * horizon_days
    sig_h = sigma_daily * np.sqrt(horizon_days)
    # VaR = -(μ + z·σ) when reporting loss as positive number.
    var = -(mu_h + z * sig_h)
    return float(max(var, 0.0))


def historical_var(returns: pd.Series, confidence: float, horizon_days: int = 1) -> float:
    """
    Historical-simulation VaR (positive loss) using the empirical quantile.
    Multi-day horizon approximates by scaling the 1-day quantile with √T.
    """
    if returns.empty:
        return 0.0
    q = float(np.quantile(returns.values, 1.0 - confidence))
    var_1d = -q
    return float(max(var_1d * np.sqrt(horizon_days), 0.0))


def conditional_var(returns: pd.Series, confidence: float) -> float:
    """
    Expected Shortfall / CVaR: mean loss beyond the VaR threshold (1-day).
    """
    if returns.empty:
        return 0.0
    threshold = np.quantile(returns.values, 1.0 - confidence)
    tail = returns[returns <= threshold]
    if tail.empty:
        return float(max(-threshold, 0.0))
    return float(max(-tail.mean(), 0.0))


def max_drawdown(returns: pd.Series) -> float:
    """Maximum peak-to-trough drawdown on a compounded wealth path."""
    if returns.empty:
        return 0.0
    wealth = np.exp(returns.cumsum())
    peak = np.maximum.accumulate(wealth.values)
    dd = (wealth.values - peak) / peak
    return float(abs(dd.min())) if len(dd) else 0.0


def sortino_ratio(
    returns: pd.Series,
    risk_free: float = RISK_FREE_RATE,
    trading_days: int = TRADING_DAYS,
) -> float:
    """Annualized Sortino ratio using downside deviation vs daily RF."""
    if returns.empty:
        return 0.0
    rf_daily = risk_free / trading_days
    excess = returns - rf_daily
    downside = excess[excess < 0.0]
    if downside.empty:
        return float("inf") if excess.mean() > 0 else 0.0
    downside_dev = float(np.sqrt(np.mean(downside.values ** 2)))
    if downside_dev < 1e-18:
        return 0.0
    return float((excess.mean() * trading_days) / (downside_dev * np.sqrt(trading_days)))


def compute_portfolio_risk_metrics(
    log_returns: pd.DataFrame,
    weights: pd.Series,
    risk_free: float = RISK_FREE_RATE,
) -> Dict[str, float]:
    """
    Full risk dashboard for a weight vector.

    Returns parametric VaR (95/99 × 1d/30d), historical VaR (95/99),
    CVaR 95/99, max drawdown, and Sortino ratio.
    """
    port = _portfolio_daily_returns(log_returns, weights)
    mu_d = float(port.mean())
    sig_d = float(port.std(ddof=1))

    metrics = {
        "daily_mean": mu_d,
        "daily_vol": sig_d,
        "ann_return": mu_d * TRADING_DAYS,
        "ann_vol": sig_d * np.sqrt(TRADING_DAYS),
        "parametric_var_95_1d": parametric_var(mu_d, sig_d, 0.95, 1),
        "parametric_var_99_1d": parametric_var(mu_d, sig_d, 0.99, 1),
        "parametric_var_95_30d": parametric_var(mu_d, sig_d, 0.95, 30),
        "parametric_var_99_30d": parametric_var(mu_d, sig_d, 0.99, 30),
        "historical_var_95_1d": historical_var(port, 0.95, 1),
        "historical_var_99_1d": historical_var(port, 0.99, 1),
        "historical_var_95_30d": historical_var(port, 0.95, 30),
        "historical_var_99_30d": historical_var(port, 0.99, 30),
        "cvar_95": conditional_var(port, 0.95),
        "cvar_99": conditional_var(port, 0.99),
        "max_drawdown": max_drawdown(port),
        "sortino": sortino_ratio(port, risk_free),
    }
    # Sharpe from annualized moments.
    if metrics["ann_vol"] > 1e-12:
        metrics["sharpe"] = (metrics["ann_return"] - risk_free) / metrics["ann_vol"]
    else:
        metrics["sharpe"] = 0.0
    return metrics
