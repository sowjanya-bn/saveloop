from __future__ import annotations

from pathlib import Path

import pandas as pd

from saveloop.config import project_paths


REQUIRED_TREND_COLUMNS = [
    "source",
    "theme",
    "keyword",
    "momentum_score",
    "observed_at",
    "notes",
]


def load_trends(path: Path | None = None) -> pd.DataFrame:
    paths = project_paths()
    path = path or (paths["raw_data_dir"] / "trends_snapshot.csv")
    if not path.exists():
        raise SystemExit(f"Trend snapshot not found: {path}")

    df = pd.read_csv(path)
    missing = [column for column in REQUIRED_TREND_COLUMNS if column not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns in trends snapshot: {', '.join(missing)}")

    df["momentum_score"] = pd.to_numeric(df["momentum_score"], errors="coerce").fillna(0.0)
    for column in ["source", "theme", "keyword", "observed_at", "notes"]:
        df[column] = df[column].fillna("").astype(str).str.strip()

    return df
