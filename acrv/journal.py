"""Trade journal: log ideas in journal/trades.csv, mark them to market.

Columns in trades.csv
---------------------
id, open_date, instrument, direction, entry_bp, target_bp, stop_bp,
thesis, close_date, exit_bp, close_reason

direction is one of: tighter, wider, flattener, steepener.
P&L is in basis points of the instrument (not dollars): a 'tighter' trade
entered at 150 and marked at 140 is +10bp.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .screen import FALL, RISE

COLUMNS = ["id", "open_date", "instrument", "direction", "entry_bp", "target_bp", "stop_bp",
           "thesis", "close_date", "exit_bp", "close_reason"]
JOURNAL_DIR = Path(__file__).resolve().parent.parent / "journal"


def pnl_bp(direction: str, entry: float, mark: float) -> float:
    if direction in FALL:
        return entry - mark
    if direction in RISE:
        return mark - entry
    raise ValueError(f"unknown direction {direction!r}; use one of {sorted(FALL | RISE)}")


def load_trades(path: Path = JOURNAL_DIR / "trades.csv") -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLUMNS)
    text_cols = ["id", "open_date", "instrument", "direction", "thesis", "close_date", "close_reason"]
    df = pd.read_csv(path, dtype={c: "object" for c in text_cols})
    for c in COLUMNS:
        if c not in df:
            df[c] = np.nan
    for c in ["entry_bp", "target_bp", "stop_bp", "exit_bp"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[COLUMNS]


def mark_to_market(trades: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    """Add mark, P&L and status. Open trades that touched target/stop are auto-flagged."""
    out = trades.copy()
    marks, pnls, status, mfe, mae = [], [], [], [], []
    for _, t in out.iterrows():
        s = panel.get(t["instrument"])
        is_closed = pd.notna(t["exit_bp"])
        if s is None or s.dropna().empty:
            marks.append(np.nan); pnls.append(np.nan); mfe.append(np.nan); mae.append(np.nan)
            status.append("closed" if is_closed else "no data")
            continue
        s = s.dropna()
        start = pd.Timestamp(t["open_date"])
        end = pd.Timestamp(t["close_date"]) if is_closed and pd.notna(t["close_date"]) else s.index[-1]
        path = s[(s.index >= start) & (s.index <= end)]
        mark = float(t["exit_bp"]) if is_closed else float(s.iloc[-1])
        path_pnl = path.apply(lambda m: pnl_bp(t["direction"], t["entry_bp"], m))
        marks.append(mark)
        pnls.append(pnl_bp(t["direction"], t["entry_bp"], mark))
        mfe.append(float(path_pnl.max()) if len(path_pnl) else np.nan)  # best it got
        mae.append(float(path_pnl.min()) if len(path_pnl) else np.nan)  # worst it got
        if is_closed:
            status.append("closed")
        else:
            hit_target = pd.notna(t["target_bp"]) and len(path_pnl) and \
                path_pnl.max() >= pnl_bp(t["direction"], t["entry_bp"], t["target_bp"])
            hit_stop = pd.notna(t["stop_bp"]) and len(path_pnl) and \
                path_pnl.min() <= pnl_bp(t["direction"], t["entry_bp"], t["stop_bp"])
            status.append("STOP HIT - close it" if hit_stop else "TARGET HIT - close it" if hit_target else "open")
    out["mark_bp"] = marks
    out["pnl_bp"] = pnls
    out["best_bp"] = mfe
    out["worst_bp"] = mae
    out["status"] = status
    return out


def summary(marked: pd.DataFrame) -> dict:
    closed = marked[marked["status"] == "closed"]
    return {
        "trades": len(marked),
        "open": int((marked["status"] != "closed").sum()),
        "closed": len(closed),
        "hit_rate_pct": float((closed["pnl_bp"] > 0).mean() * 100) if len(closed) else np.nan,
        "avg_pnl_bp": float(closed["pnl_bp"].mean()) if len(closed) else np.nan,
        "total_pnl_bp": float(marked["pnl_bp"].sum(skipna=True)),
    }
