"""Export utilities for portfolio tear-sheets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import pandas as pd


def build_tearsheet_payload(
    weights: pd.Series,
    metrics: Dict[str, float],
    method: str,
    tickers_meta: Dict[str, Any],
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble a JSON-serializable tear-sheet dictionary."""
    payload: Dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": "NSE Quant Risk Terminal",
        "optimization_method": method,
        "weights": {str(k): float(v) for k, v in weights.items()},
        "risk_metrics": {str(k): _to_native(v) for k, v in metrics.items()},
        "universe_meta": tickers_meta,
        "disclaimer": (
            "Educational analytical output only. Not SEBI-registered advice. "
            "Past performance is non-indicative of future results."
        ),
    }
    if extra:
        payload["extras"] = {str(k): _to_native(v) for k, v in extra.items()}
    return payload


def tearsheet_to_json(payload: Dict[str, Any]) -> str:
    """Pretty-printed JSON for download buttons."""
    return json.dumps(payload, indent=2, default=_json_default)


def tearsheet_to_csv(payload: Dict[str, Any]) -> str:
    """
    Flatten weights + key metrics into a two-column CSV string
    suitable for ``st.download_button``.
    """
    rows = []
    rows.append({"section": "meta", "key": "generated_at_utc", "value": payload.get("generated_at_utc")})
    rows.append({"section": "meta", "key": "optimization_method", "value": payload.get("optimization_method")})
    for k, v in (payload.get("weights") or {}).items():
        rows.append({"section": "weights", "key": k, "value": v})
    for k, v in (payload.get("risk_metrics") or {}).items():
        rows.append({"section": "risk_metrics", "key": k, "value": v})
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def _to_native(v: Any) -> Any:
    if isinstance(v, (pd.Series, pd.DataFrame)):
        return v.to_dict()
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:  # noqa: BLE001
            return float(v) if hasattr(v, "__float__") else str(v)
    if isinstance(v, float) and (v != v):  # NaN
        return None
    return v


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return str(obj)
