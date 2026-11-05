"""Command line entry point.

    python -m acrv screen            # pull FRED, run the screen, write reports/screen.md
    python -m acrv screen --demo     # same on simulated data (no internet needed)
    python -m acrv journal           # mark journal/trades.csv to market, write journal/JOURNAL.md
"""
from __future__ import annotations

import argparse

import pandas as pd

from . import journal as J
from .data import build_instruments, load_raw
from .report import write_journal_report, write_screen_report
from .screen import build_screen


def main(argv=None):
    p = argparse.ArgumentParser(prog="acrv", description="Asia credit & rates RV screen + trade journal")
    sub = p.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("screen", help="run the RV screen")
    sc.add_argument("--demo", action="store_true", help="use simulated data")
    sc.add_argument("--threshold", type=float, default=2.0, help="|z| to flag (default 2)")
    jn = sub.add_parser("journal", help="mark the trade journal to market")
    jn.add_argument("--demo", action="store_true", help="use simulated data")
    op = sub.add_parser("open", help="log a new trade at today's level")
    op.add_argument("instrument", help="e.g. ASIA_vs_EM, UST_2s10s (see reports/screen.csv)")
    op.add_argument("direction", choices=["tighter", "wider", "flattener", "steepener"])
    op.add_argument("--thesis", required=True, help="why, in one or two sentences")
    op.add_argument("--target", type=float, help="target level in bp (default: screen's 1y mean)")
    op.add_argument("--stop", type=float, help="stop level in bp (default: screen's stop)")
    op.add_argument("--demo", action="store_true", help="use simulated data")
    cl = sub.add_parser("close", help="close an open trade at today's level")
    cl.add_argument("id")
    cl.add_argument("--reason", required=True)
    cl.add_argument("--demo", action="store_true", help="use simulated data")
    args = p.parse_args(argv)

    source = "synthetic" if args.demo else "fred"
    panel = build_instruments(load_raw(source))

    if args.cmd == "screen":
        screen = build_screen(panel, threshold=args.threshold)
        path = write_screen_report(screen, panel, source=source)
        with pd.option_context("display.width", 160, "display.max_columns", 20):
            print(screen[["label", "level_bp", "z_1y", "pctile_hist", "half_life_d", "flag"]].round(1).to_string())
        print(f"\nReport: {path}")
    elif args.cmd == "open":
        if args.instrument not in panel:
            raise SystemExit(f"unknown instrument {args.instrument}; choose from {list(panel.columns)}")
        row = build_screen(panel, threshold=0).set_index("instrument").loc[args.instrument]
        trades = J.load_trades()
        new_id = str(len(trades) + 1)
        trade = {"id": new_id, "open_date": str(row["as_of"]), "instrument": args.instrument,
                 "direction": args.direction, "entry_bp": round(row["level_bp"], 1),
                 "target_bp": args.target if args.target is not None else round(row["target_bp"], 1),
                 "stop_bp": args.stop if args.stop is not None else round(row["stop_bp"], 1),
                 "thesis": args.thesis}
        trades = pd.concat([trades, pd.DataFrame([trade])], ignore_index=True)[J.COLUMNS]
        trades.to_csv(J.JOURNAL_DIR / "trades.csv", index=False)
        print(f"Logged #{new_id}: {args.direction} {args.instrument} @ {trade['entry_bp']}bp "
              f"(target {trade['target_bp']}, stop {trade['stop_bp']})")
    elif args.cmd == "close":
        trades = J.load_trades()
        hit = trades["id"] == args.id
        if not hit.any():
            raise SystemExit(f"no trade #{args.id}")
        inst = trades.loc[hit, "instrument"].iloc[0]
        s = panel[inst].dropna()
        trades.loc[hit, ["close_date", "exit_bp", "close_reason"]] = [str(s.index[-1].date()),
                                                                       round(float(s.iloc[-1]), 1), args.reason]
        trades.to_csv(J.JOURNAL_DIR / "trades.csv", index=False)
        print(f"Closed #{args.id} {inst} @ {s.iloc[-1]:.1f}bp")
    else:
        trades = J.load_trades()
        marked = J.mark_to_market(trades, panel)
        stats = J.summary(marked)
        path = write_journal_report(marked, stats, J.JOURNAL_DIR / "JOURNAL.md")
        print(stats)
        print(f"Journal: {path}")


if __name__ == "__main__":
    main()
