import numpy as np
import pandas as pd
import pytest

from acrv import signals as S
from acrv.data import _parse_fred_csv, build_instruments
from acrv.screen import build_screen
from acrv.synthetic import ou_path, synthetic_raw


def _series(values):
    return pd.Series(values, index=pd.bdate_range("2024-01-01", periods=len(values)), dtype=float)


def test_zscore_of_spike_is_large():
    s = _series([100.0] * 200 + [101.0, 99.0] * 30 + [130.0])
    assert S.rolling_zscore(s).iloc[-1] > 5


def test_percentile_rank_bounds():
    s = _series(range(100))
    assert S.percentile_rank(s) == 100
    assert S.percentile_rank(s[::-1].reset_index(drop=True)) == 1


def test_change():
    s = _series(range(30))
    assert S.change(s, 5) == 5
    assert np.isnan(S.change(s, 50))


def test_half_life_recovers_known_speed():
    rng = np.random.default_rng(0)
    kappa = 0.05  # true half-life = ln2 / -ln(1-0.05) ~ 13.5 days
    s = _series(ou_path(2000, 100, 1.0, kappa, rng))
    hl = S.half_life(s, window=None)
    assert 9 < hl < 20


def test_half_life_random_walk_is_slow():
    rng = np.random.default_rng(1)
    s = _series(np.cumsum(rng.standard_normal(1000)) + 100)
    assert S.half_life(s, window=None) > 30


def test_parse_fred_csv_handles_missing(tmp_path):
    p = tmp_path / "X.csv"
    p.write_text("observation_date,X\n2026-01-01,1.50\n2026-01-02,.\n2026-01-05,1.55\n")
    s = _parse_fred_csv(p, "X")
    assert list(s.values) == [1.50, 1.55]


def test_instruments_units_in_bp():
    raw = pd.DataFrame({"UST2": [4.00], "UST5": [4.10], "UST10": [4.50], "UST30": [4.80],
                        "ASIA_EM": [120.0], "EM_CORP": [150.0]},
                       index=pd.to_datetime(["2026-11-04"]))
    p = build_instruments(raw)
    assert p["UST_2s10s"].iloc[0] == pytest.approx(50)
    assert p["UST_2s5s10s"].iloc[0] == pytest.approx(-30)  # 2*4.10 - 4.00 - 4.50
    assert p["ASIA_vs_EM"].iloc[0] == pytest.approx(-30)


def test_screen_runs_and_flags_on_synthetic():
    panel = build_instruments(synthetic_raw())
    scr = build_screen(panel)
    assert len(scr) == panel.shape[1]
    assert scr["z_1y"].abs().is_monotonic_decreasing
    flagged = scr[scr["flag"].isin(["CHEAP", "RICH", "STEEP", "FLAT", "BELLY CHEAP", "BELLY RICH"])]
    # target sits on the mean; stop sits on the other side of entry
    for _, r in flagged.iterrows():
        assert np.sign(r["target_bp"] - r["level_bp"]) == -np.sign(r["stop_bp"] - r["level_bp"])
