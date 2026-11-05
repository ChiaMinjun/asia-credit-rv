import numpy as np
import pandas as pd
import pytest

from acrv import journal as J


def test_pnl_signs():
    assert J.pnl_bp("tighter", 150, 140) == 10
    assert J.pnl_bp("wider", 150, 140) == -10
    assert J.pnl_bp("flattener", 60, 50) == 10
    assert J.pnl_bp("steepener", 60, 50) == -10
    with pytest.raises(ValueError):
        J.pnl_bp("long", 1, 2)


def _panel():
    idx = pd.bdate_range("2026-10-01", periods=10)
    return pd.DataFrame({"ASIA_vs_EM": [-20, -22, -25, -30, -28, -26, -24, -21, -19, -18]}, index=idx)


def _trade(**kw):
    base = dict(id="1", open_date="2026-10-01", instrument="ASIA_vs_EM", direction="wider",
                entry_bp=-20.0, target_bp=-10.0, stop_bp=-29.0, thesis="t",
                close_date=np.nan, exit_bp=np.nan, close_reason=np.nan)
    base.update(kw)
    return pd.DataFrame([base])


def test_open_trade_marks_and_flags_stop():
    m = J.mark_to_market(_trade(), _panel())
    r = m.iloc[0]
    assert r["mark_bp"] == -18 and r["pnl_bp"] == 2
    assert r["worst_bp"] == -10  # went to -30 against us
    assert r["status"].startswith("STOP HIT")


def test_closed_trade_uses_exit():
    m = J.mark_to_market(_trade(close_date="2026-10-03", exit_bp=-25.0, close_reason="stopped"), _panel())
    r = m.iloc[0]
    assert r["status"] == "closed" and r["pnl_bp"] == -5
    s = J.summary(m)
    assert s["closed"] == 1 and s["hit_rate_pct"] == 0
