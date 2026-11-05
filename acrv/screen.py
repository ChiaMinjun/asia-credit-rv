"""The RV screen: one row per instrument, flagged when stretched vs history."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import signals as S
from . import universe as U
from .data import instrument_kind

# Directions that make money when the line FALLS vs RISES (in bp).
FALL = {"tighter", "flattener"}
RISE = {"wider", "steepener"}


def _view(name: str, z: float, threshold: float) -> tuple[str, str]:
    """Return (flag, trade idea in words) for a stretched instrument."""
    if np.isnan(z) or abs(z) < threshold:
        return "", ""
    kind = instrument_kind(name)
    high = z > 0
    if kind == "outright":
        return ("CHEAP", "spread wide vs 1y: look for tighter (buy risk)") if high else (
            "RICH", "spread tight vs 1y: look for wider (sell risk / buy protection)")
    if kind == "pair":
        a, b, _ = U.PAIRS[name]
        return ("CHEAP", f"{a} cheap vs {b}: long {a} / short {b}, play for tighter") if high else (
            "RICH", f"{a} rich vs {b}: short {a} / long {b}, play for wider")
    if kind == "curve":
        if U.CURVES[name][0] == "fly":
            return ("BELLY CHEAP", "belly yield high vs wings: buy the belly, play fly tighter") if high else (
                "BELLY RICH", "belly yield low vs wings: sell the belly, play fly wider")
        return ("STEEP", "curve steep vs 1y: flattener") if high else ("FLAT", "curve flat vs 1y: steepener")
    return "", ""


def suggested_direction(name: str, z: float) -> str:
    kind = instrument_kind(name)
    if kind == "curve" and U.CURVES[name][0] == "slope":
        return "flattener" if z > 0 else "steepener"
    return "tighter" if z > 0 else "wider"


def build_screen(panel: pd.DataFrame, z_window: int = 252, threshold: float = 2.0,
                 watch: float = 1.5) -> pd.DataFrame:
    rows = []
    for name in panel.columns:
        s = panel[name].dropna()
        if len(s) < 60:
            continue
        z_series = S.rolling_zscore(s, z_window)
        z = float(z_series.iloc[-1])
        mean = float(s.iloc[-z_window:].mean())
        flag, idea = _view(name, z, threshold)
        if not flag and abs(z) >= watch:
            flag = "watch"
        level = float(s.iloc[-1])
        # Mechanical trade levels: target = back to the 1y mean, stop = half the
        # distance beyond entry (2:1 reward/risk), never tighter than 1.5x the
        # typical daily move. A starting point to sanity-check, not a rule.
        vol = S.realised_vol(s)
        dist = mean - level
        stop_dist = max(abs(dist) / 2, 1.5 * vol) if not np.isnan(vol) else abs(dist) / 2
        rows.append({
            "instrument": name,
            "label": U.label(name),
            "kind": instrument_kind(name),
            "level_bp": level,
            "chg_1w_bp": S.change(s, 5),
            "chg_1m_bp": S.change(s, 21),
            "mean_1y_bp": mean,
            "z_1y": z,
            "pctile_hist": S.percentile_rank(s),
            "half_life_d": S.half_life(s, z_window),
            "vol_daily_bp": vol,
            "flag": flag,
            "idea": idea,
            "target_bp": mean if flag and flag != "watch" else np.nan,
            "stop_bp": level - np.sign(dist) * stop_dist if flag and flag != "watch" else np.nan,
            "as_of": s.index[-1].date(),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.reindex(df["z_1y"].abs().sort_values(ascending=False).index).reset_index(drop=True)
