"""Simulated market data for tests and offline demos.

Each series is a mean-reverting (Ornstein-Uhlenbeck) process around a
plausible level. These numbers are NOT real market data.
"""
import numpy as np
import pandas as pd

from . import universe as U

# key -> (long-run level, daily vol, mean-reversion speed per day)
_PARAMS = {
    "ASIA_EM": (120, 2.5, 0.02),
    "ASIA_EM_LIQ": (115, 2.5, 0.02),
    "LATAM_EM": (280, 4.0, 0.02),
    "EMEA_EM": (170, 3.0, 0.02),
    "EM_CORP": (160, 2.8, 0.02),
    "EM_HG": (95, 1.8, 0.02),
    "EM_HY": (330, 6.0, 0.015),
    "US_IG": (85, 1.5, 0.02),
    "US_BBB": (105, 1.8, 0.02),
    "US_HY": (310, 6.0, 0.015),
    "UST2": (3.8, 0.05, 0.005),
    "UST5": (3.9, 0.05, 0.005),
    "UST10": (4.2, 0.05, 0.005),
    "UST30": (4.6, 0.045, 0.005),
}


def ou_path(n, level, vol, kappa, rng, common=None, beta=0.0):
    x = np.empty(n)
    x[0] = level
    shocks = rng.standard_normal(n)
    for t in range(1, n):
        shock = vol * shocks[t]
        if common is not None:
            shock = vol * (beta * common[t] + np.sqrt(1 - beta**2) * shocks[t])
        x[t] = x[t - 1] + kappa * (level - x[t - 1]) + shock
    return x


def synthetic_raw(n_days: int = 780, seed: int = 7, end: str = "2026-11-04") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=end, periods=n_days)
    credit_factor = rng.standard_normal(n_days)  # spreads move together
    rates_factor = rng.standard_normal(n_days)  # so do yields
    data = {}
    for key, (lvl, vol, k) in _PARAMS.items():
        common = rates_factor if key in U.RATES else credit_factor
        data[key] = ou_path(n_days, lvl, vol, k, rng, common=common, beta=0.8)
    return pd.DataFrame(data, index=idx)
