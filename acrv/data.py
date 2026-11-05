"""Download and cache FRED series; build the instrument panel in bp."""
from __future__ import annotations

import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from . import universe as U

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def _parse_fred_csv(path: Path, sid: str) -> pd.Series:
    df = pd.read_csv(path, na_values=["."])
    date_col = df.columns[0]  # "observation_date" (new) or "DATE" (old)
    val_col = sid if sid in df.columns else df.columns[1]
    s = pd.Series(
        pd.to_numeric(df[val_col], errors="coerce").values,
        index=pd.to_datetime(df[date_col]),
        name=sid,
    )
    return s.dropna().sort_index()


def fetch_series(sid: str, cache_dir: Path = DATA_DIR, max_age_hours: float = 12) -> pd.Series:
    """Return one FRED series, using a local cache to avoid re-downloading."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{sid}.csv"
    fresh = path.exists() and (time.time() - path.stat().st_mtime) < max_age_hours * 3600
    if not fresh:
        req = urllib.request.Request(FRED_CSV.format(sid=sid), headers={"User-Agent": "asia-credit-rv"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                path.write_bytes(r.read())
        except Exception as e:  # network down: fall back to stale cache if we have one
            if not path.exists():
                raise RuntimeError(f"Could not download {sid} and no cached copy: {e}") from e
            print(f"warning: using cached {sid} ({e})")
    return _parse_fred_csv(path, sid)


def load_raw(source: str = "fred") -> pd.DataFrame:
    """Raw panel keyed by universe names. Credit in bp, rates in percent."""
    if source == "synthetic":
        from .synthetic import synthetic_raw
        return synthetic_raw()
    cols = {}
    for key, sid in U.all_series_ids().items():
        try:
            cols[key] = fetch_series(sid)
        except Exception as e:
            print(f"warning: skipping {key} ({sid}): {e}")
    if not cols:
        raise SystemExit("No data downloaded from FRED. Check your internet connection, "
                         "or run with --demo to use simulated data.")
    raw = pd.DataFrame(cols)
    for key in U.CREDIT:
        if key in raw:
            raw[key] = raw[key] * 100.0  # percent -> bp
    return raw


def build_instruments(raw: pd.DataFrame) -> pd.DataFrame:
    """Every tradeable line on the screen, in basis points, business-day aligned."""
    raw = raw.sort_index().ffill(limit=3)  # bridge holidays where one market is shut
    out = {}
    for key in U.CREDIT:
        if key in raw:
            out[key] = raw[key]
    for name, (a, b, _) in U.PAIRS.items():
        if a in raw and b in raw:
            out[name] = raw[a] - raw[b]
    for name, (kind, legs, _) in U.CURVES.items():
        if not all(l in raw for l in legs):
            continue
        if kind == "slope":
            out[name] = (raw[legs[1]] - raw[legs[0]]) * 100.0
        else:
            w1, belly, w2 = legs
            out[name] = (2 * raw[belly] - raw[w1] - raw[w2]) * 100.0
    panel = pd.DataFrame(out)
    panel = panel[panel.index.dayofweek < 5]
    return panel.replace([np.inf, -np.inf], np.nan)


def instrument_kind(name: str) -> str:
    if name in U.CREDIT:
        return "outright"
    if name in U.PAIRS:
        return "pair"
    if name in U.CURVES:
        return "curve"
    return "other"
