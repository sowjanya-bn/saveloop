from __future__ import annotations

import pandas as pd


def summarize_experiments(experiments_df: pd.DataFrame) -> dict[str, int]:
    if experiments_df.empty:
        return {"open": 0, "total": 0}
    status_column = "status" if "status" in experiments_df.columns else None
    if status_column is None:
        return {"open": 0, "total": len(experiments_df)}
    open_count = int(experiments_df[experiments_df[status_column].astype(str).str.lower() != "done"].shape[0])
    return {"open": open_count, "total": len(experiments_df)}
