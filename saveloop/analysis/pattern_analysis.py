from __future__ import annotations

import pandas as pd


def best_pattern(pattern_performance: pd.DataFrame) -> pd.Series | None:
    if pattern_performance.empty:
        return None
    return pattern_performance.sort_values("J_mean", ascending=False).iloc[0]
