from __future__ import annotations

import pandas as pd


def score_trends(trends_df: pd.DataFrame) -> pd.DataFrame:
    if trends_df.empty:
        return trends_df.copy()

    scored = trends_df.copy()
    scored["trend_score"] = scored["momentum_score"].clip(lower=0.0, upper=1.0)
    scored = scored.sort_values(["trend_score", "keyword"], ascending=[False, True]).reset_index(drop=True)
    return scored
