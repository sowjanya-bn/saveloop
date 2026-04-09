from __future__ import annotations

import pandas as pd


def best_tag(tag_performance: pd.DataFrame, min_count: int = 2) -> pd.Series | None:
    if tag_performance.empty:
        return None
    eligible = tag_performance[tag_performance["count"] >= min_count]
    if eligible.empty:
        return None
    return eligible.sort_values("J_mean", ascending=False).iloc[0]
