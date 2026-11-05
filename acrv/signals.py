"""Relative-value statistics. Each function takes a pd.Series in bp."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_zscore(s: pd.Series, window: int = 252, min_periods: int = 60) -> pd.Series:
    """How many standard deviations today's level is from its rolling mean."""
    mean = s.rolling(window, min_periods=min_periods).mean()
    std = s.rolling(window, min_periods=min_periods).std()
    return (s - mean) / std


def percentile_rank(s: pd.Series) -> float:
    """Where the latest value sits in its full history, 0-100."""
    s = s.dropna()
    if s.empty:
        return np.nan
    return float((s <= s.iloc[-1]).mean() * 100)


def change(s: pd.Series, days: int) -> float:
    """Change in bp over the last `days` business days."""
    s = s.dropna()
    if len(s) <= days:
        return np.nan
    return float(s.iloc[-1] - s.iloc[-1 - days])


def half_life(s: pd.Series, window: int | None = 252) -> float:
    """Mean-reversion half-life in business days, from an AR(1) fit.

    Regress  dx_t = a + b * x_{t-1}.  If b < 0 the series pulls back to its
    mean, and the half-life is  -ln(2) / ln(1 + b).  If b >= 0 there is no
    evidence of mean reversion and we return inf.
    """
    s = s.dropna()
    if window:
        s = s.iloc[-window:]
    if len(s) < 30:
        return np.nan
    x_lag = s.shift(1).iloc[1:].values
    dx = s.diff().iloc[1:].values
    b = np.polyfit(x_lag, dx, 1)[0]
    if b >= 0 or b <= -1:
        return np.inf
    return float(-np.log(2) / np.log(1 + b))


def realised_vol(s: pd.Series, days: int = 63) -> float:
    """Std dev of daily changes in bp over the last `days`; used to size stops."""
    d = s.dropna().diff().iloc[-days:]
    return float(d.std()) if len(d) > 5 else np.nan
