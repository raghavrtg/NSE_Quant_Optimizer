"""
AI Rule-Based Allocator — lifecycle risk-parity heuristics.

Maps investor age, horizon, risk tolerance, and primary objective into a
baseline Equity / Debt / Gold / REITs mix, then optionally projects that mix
onto a concrete ticker sleeve when holdings are available.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config.settings import TICKER_ASSET_CLASS


@dataclass(frozen=True)
class AllocationAdvice:
    """Structured recommendation returned to the UI and export layer."""

    equity: float
    debt: float
    gold: float
    reits: float
    profile_label: str
    rationale: str
    risk_score: float  # 0 (capital preservation) → 100 (aggressive growth)

    def as_series(self) -> pd.Series:
        return pd.Series(
            {
                "Equity": self.equity,
                "Debt": self.debt,
                "Gold": self.gold,
                "REITs": self.reits,
            },
            name="Target Weights",
        )

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(max(lo, min(hi, x)))


def recommend_allocation(
    age: int,
    horizon_years: int,
    risk_tolerance: str,
    primary_objective: str,
) -> AllocationAdvice:
    """
    Generate a baseline asset-class distribution.

    Heuristic
    ---------
    * Lifecycle glide: equity bias declines with age (100 − age), floored.
    * Horizon extends equity runway (longer → more growth assets).
    * Risk tolerance scales equity / alternatives vs debt.
    * Objective nudges income sleeves (Debt + REITs) vs wealth creation.
    """
    if age < 18 or age > 100:
        raise ValueError("Age must be between 18 and 100.")
    if horizon_years < 1 or horizon_years > 50:
        raise ValueError("Investment horizon must be between 1 and 50 years.")

    tol = risk_tolerance.strip().lower()
    obj = primary_objective.strip().lower()

    # --- Risk score ---------------------------------------------------------
    base_glide = _clamp((100 - age) / 100.0, 0.15, 0.90)
    horizon_boost = _clamp(horizon_years / 40.0, 0.0, 0.25)

    tol_map = {
        "capital preservation": -0.35,
        "conservative": -0.20,
        "moderate": 0.0,
        "aggressive": 0.25,
    }
    tol_adj = tol_map.get(tol, 0.0)

    obj_equity_adj = {
        "wealth creation": 0.10,
        "retirement": 0.0,
        "regular income": -0.15,
    }.get(obj, 0.0)

    equity = _clamp(base_glide + horizon_boost + tol_adj + obj_equity_adj, 0.05, 0.90)

    # Residual sleeve split among Debt / Gold / REITs.
    residual = 1.0 - equity
    if obj == "regular income":
        debt_share, gold_share, reit_share = 0.55, 0.15, 0.30
    elif obj == "retirement":
        debt_share, gold_share, reit_share = 0.50, 0.20, 0.30
    else:  # wealth creation
        debt_share, gold_share, reit_share = 0.35, 0.30, 0.35

    # Capital preservation pulls harder into debt / gold.
    if tol in ("capital preservation", "conservative"):
        debt_share += 0.10
        gold_share += 0.05
        reit_share -= 0.15
        total_alt = debt_share + gold_share + reit_share
        debt_share /= total_alt
        gold_share /= total_alt
        reit_share /= total_alt

    debt = residual * debt_share
    gold = residual * gold_share
    reits = residual * reit_share

    # Renormalize for floating-point safety.
    total = equity + debt + gold + reits
    equity, debt, gold, reits = (
        equity / total,
        debt / total,
        gold / total,
        reits / total,
    )

    risk_score = _clamp(
        (equity * 100) + (tol_adj * 40) + (horizon_boost * 30),
        0,
        100,
    )

    profile_label = f"{risk_tolerance.title()} · {primary_objective.title()}"
    rationale = (
        f"At age {age} with a {horizon_years}-year horizon and a "
        f"{risk_tolerance.lower()} stance oriented toward {primary_objective.lower()}, "
        f"lifecycle risk-parity allocates {equity:.0%} to equities, {debt:.0%} to "
        f"debt / G-Secs, {gold:.0%} to gold / commodities, and {reits:.0%} to "
        f"REITs / InvITs. Longer horizons and higher risk tolerance increase the "
        f"equity sleeve; income objectives raise debt and REIT weights."
    )

    return AllocationAdvice(
        equity=equity,
        debt=debt,
        gold=gold,
        reits=reits,
        profile_label=profile_label,
        rationale=rationale,
        risk_score=risk_score,
    )


def map_advice_to_tickers(
    advice: AllocationAdvice,
    tickers: List[str],
) -> pd.Series:
    """
    Project asset-class targets onto the selected ticker sleeve.

    Tickers within each class receive equal weight of that class budget.
    Unmapped tickers inherit a tiny residual slice of Equity.
    """
    class_budget = {
        "Equity": advice.equity,
        "Debt": advice.debt,
        "Gold": advice.gold,
        "REITs": advice.reits,
    }
    buckets: Dict[str, List[str]] = {k: [] for k in class_budget}
    unmapped: List[str] = []
    for t in tickers:
        cls = TICKER_ASSET_CLASS.get(t, "Equity")
        if cls in buckets:
            buckets[cls].append(t)
        else:
            unmapped.append(t)
    if unmapped:
        buckets["Equity"].extend(unmapped)

    weights = pd.Series(0.0, index=tickers, dtype=float)
    for cls, members in buckets.items():
        if not members:
            continue
        each = class_budget[cls] / len(members)
        for t in members:
            if t in weights.index:
                weights.loc[t] += each

    if weights.sum() <= 0:
        weights[:] = 1.0 / len(weights)
    else:
        weights = weights / weights.sum()
    weights.name = "Advisor Weights"
    return weights


def apply_stress_shock(
    mean_annual: pd.Series,
    cov_annual: pd.DataFrame,
    equity_shock: float = -0.20,
    rates_shock: float = 0.01,
    gold_shock: float = 0.05,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Scenario stress: shift expected returns by asset class and inflate
    covariance diagonals for shocked sleeves.
    """
    shocked_mu = mean_annual.copy()
    shocked_cov = cov_annual.copy()
    for t in mean_annual.index:
        cls = TICKER_ASSET_CLASS.get(str(t), "Equity")
        if cls == "Equity":
            shocked_mu.loc[t] = shocked_mu.loc[t] + equity_shock
            shocked_cov.loc[t, t] = shocked_cov.loc[t, t] * 1.5
        elif cls == "Debt":
            # Rising rates → negative for bonds; model via return haircut.
            shocked_mu.loc[t] = shocked_mu.loc[t] - abs(rates_shock) * 2.0
            shocked_cov.loc[t, t] = shocked_cov.loc[t, t] * 1.25
        elif cls == "Gold":
            shocked_mu.loc[t] = shocked_mu.loc[t] + gold_shock
        elif cls == "REITs":
            shocked_mu.loc[t] = shocked_mu.loc[t] + equity_shock * 0.6
            shocked_cov.loc[t, t] = shocked_cov.loc[t, t] * 1.35
    shocked_cov = 0.5 * (shocked_cov + shocked_cov.T)
    return shocked_mu, shocked_cov
