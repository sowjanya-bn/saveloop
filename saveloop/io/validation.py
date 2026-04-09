from __future__ import annotations

from typing import Iterable

import pandas as pd

REQUIRED_POST_COLUMNS = [
    "post_id",
    "bundle_id",
    "date_posted",
    "format",
    "pattern",
    "aesthetic_tags",
    "views",
    "reach",
    "likes",
    "comments",
    "saves",
    "shares",
    "profile_visits",
    "follows",
    "avg_view_duration_s",
    "replays",
    "dms_started",
    "note",
]

NUMERIC_COLUMNS = [
    "views",
    "reach",
    "likes",
    "comments",
    "saves",
    "shares",
    "profile_visits",
    "follows",
    "avg_view_duration_s",
    "replays",
    "dms_started",
]


def validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> list[str]:
    missing = [column for column in required_columns if column not in df.columns]
    return missing
