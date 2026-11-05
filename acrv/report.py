"""Write the screen and journal to markdown with charts."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from . import signals as S
from . import universe as U

REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"


def _fmt(x, nd=1):
    if x is None or (isinstance(x, float) and (np.isnan(x))):
        return ""
    if isinstance(x, float) and np.isinf(x):
        return "none"
    return f"{x:,.{nd}f}" if isinstance(x, (int, float, np.floating)) else str(x)


def _md_table(df: pd.DataFrame, cols: list[str], headers: list[str]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(_fmt(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def chart(panel: pd.DataFrame, name: str, out_dir: Path, window: int = 252) -> Path:
    s = panel[name].dropna()
    mean = s.rolling(window, min_periods=60).mean()
    std = s.rolling(window, min_periods=60).std()
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(s.index, s, lw=1.2, color="#1f4e79", label=U.label(name))
    ax.plot(mean.index, mean, lw=1, color="#888", ls="--", label="1y mean")
    ax.fill_between(s.index, mean - 2 * std, mean + 2 * std, color="#1f4e79", alpha=0.08, label="±2σ")
    ax.scatter([s.index[-1]], [s.iloc[-1]], color="#c0392b", zorder=5)
    ax.set_ylabel("bp")
    ax.set_title(f"{U.label(name)}  (z = {S.rolling_zscore(s, window).iloc[-1]:+.2f})", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="upper left", frameon=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def write_screen_report(screen: pd.DataFrame, panel: pd.DataFrame, out_dir: Path = REPORT_DIR,
                        source: str = "fred") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    as_of = screen["as_of"].max() if not screen.empty else "n/a"
    flagged = screen[screen["flag"].isin(["CHEAP", "RICH", "STEEP", "FLAT", "BELLY CHEAP", "BELLY RICH"])]
    parts = [f"# RV screen — {as_of}", ""]
    if source == "synthetic":
        parts += ["> **Demo run on simulated data. These are not real market levels.**", ""]
    parts += ["## Stretched (|z| ≥ 2)", ""]
    if flagged.empty:
        parts += ["Nothing stretched today.", ""]
    else:
        parts += [_md_table(flagged, ["label", "level_bp", "z_1y", "pctile_hist", "half_life_d", "target_bp",
                                      "stop_bp", "idea"],
                            ["Instrument", "Level", "z (1y)", "Pctile", "Half-life (d)", "Target", "Stop", "Idea"]), ""]
        for name in flagged["instrument"]:
            p = chart(panel, name, out_dir / "charts")
            parts += [f"![{name}](charts/{p.name})", ""]
    parts += ["## Full screen", "",
              _md_table(screen, ["label", "level_bp", "chg_1w_bp", "chg_1m_bp", "z_1y", "pctile_hist",
                                 "half_life_d", "vol_daily_bp", "flag"],
                        ["Instrument", "Level", "1w Δ", "1m Δ", "z (1y)", "Pctile", "Half-life (d)",
                         "Daily vol", "Flag"]),
              "", "All values in basis points. Pairs = first leg minus second leg. "
              "Half-life 'none' = no evidence of mean reversion over the last year.", ""]
    path = out_dir / "screen.md"
    path.write_text("\n".join(parts))
    screen.to_csv(out_dir / "screen.csv", index=False)
    return path


def write_journal_report(marked: pd.DataFrame, stats: dict, out_path: Path) -> Path:
    parts = ["# Trade journal", "",
             f"Trades: {stats['trades']} · Open: {stats['open']} · Closed: {stats['closed']} · "
             f"Hit rate: {_fmt(stats['hit_rate_pct'], 0)}% · Avg closed P&L: {_fmt(stats['avg_pnl_bp'])}bp", ""]
    if marked.empty:
        parts += ["No trades logged yet. Add rows to `journal/trades.csv`."]
    else:
        parts += [_md_table(marked, ["id", "open_date", "instrument", "direction", "entry_bp", "mark_bp", "pnl_bp",
                                     "best_bp", "worst_bp", "status"],
                            ["#", "Opened", "Instrument", "Direction", "Entry", "Mark", "P&L (bp)", "Best", "Worst",
                             "Status"]), "", "## Theses", ""]
        for _, t in marked.iterrows():
            parts.append(f"**#{t['id']} {t['instrument']} {t['direction']}** — {t['thesis']}")
            if pd.notna(t.get("close_reason")):
                parts.append(f"  _Closed: {t['close_reason']}_")
            parts.append("")
    out_path.write_text("\n".join(parts))
    return out_path
