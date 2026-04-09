from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from saveloop.config import project_paths
from saveloop.io.validation import NUMERIC_COLUMNS, REQUIRED_POST_COLUMNS, validate_required_columns


def _coerce_float(value: object) -> float:
    try:
        if value is None:
            return math.nan
        text = str(value).strip()
        if text == "":
            return math.nan
        return float(text)
    except Exception:
        return math.nan


def load_posts_log(path: Path | None = None) -> pd.DataFrame:
    paths = project_paths()
    path = path or (paths["raw_data_dir"] / "posts_log.csv")
    if not path.exists():
        raise SystemExit(f"Posts log not found: {path}")

    df = pd.read_csv(path)
    missing = validate_required_columns(df, REQUIRED_POST_COLUMNS)
    if missing:
        raise SystemExit(f"Missing required columns in posts log: {', '.join(missing)}")

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = df[column].apply(_coerce_float)

    return df


def load_csv_if_exists(filename: str) -> pd.DataFrame:
    path = project_paths()["raw_data_dir"] / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)
