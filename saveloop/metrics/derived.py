from __future__ import annotations

import math
import re

import pandas as pd

from saveloop.config import load_metrics_config


_AFS_PATTERN = re.compile(r"AFS:\s*([0-5](?:\s*,\s*[0-5]){8})")


def parse_afs_mean(note: object) -> float:
    if not isinstance(note, str):
        return math.nan
    match = _AFS_PATTERN.search(note)
    if not match:
        return math.nan
    values = [int(part.strip()) for part in match.group(1).split(",")]
    return sum(values) / len(values) if values else math.nan


def apply_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    cfg = load_metrics_config()
    reel_threshold = cfg.get("thresholds", {}).get("reel_engagement_win", 0.005)
    carousel_threshold = cfg.get("thresholds", {}).get("carousel_engagement_win", 0.0055)

    result = df.copy()
    result["afs_mean"] = result.get("note", pd.Series([math.nan] * len(result))).apply(parse_afs_mean)

    def _win_flag(row: pd.Series) -> str:
        engagement_rate = row.get("engagement_rate")
        if pd.isna(engagement_rate):
            return ""
        post_format = str(row.get("format", "")).lower()
        threshold = carousel_threshold if post_format.startswith("carousel") else reel_threshold
        return "win" if engagement_rate >= threshold else ""

    result["win_flag"] = result.apply(_win_flag, axis=1)
    return result
