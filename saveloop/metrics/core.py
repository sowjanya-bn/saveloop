from __future__ import annotations

import math

import pandas as pd

from saveloop.config import load_metrics_config


def safe_div(numerator: object, denominator: object) -> float:
    if numerator is None or denominator is None:
        return math.nan
    if pd.isna(numerator) or pd.isna(denominator) or float(denominator) == 0:
        return math.nan
    return float(numerator) / float(denominator)


def compute_rates(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["save_rate"] = result.apply(lambda row: safe_div(row.get("saves"), row.get("views")), axis=1)
    result["comment_rate"] = result.apply(lambda row: safe_div(row.get("comments"), row.get("views")), axis=1)
    result["dm_rate"] = result.apply(lambda row: safe_div(row.get("dms_started"), row.get("profile_visits")), axis=1)
    result["hook_efficiency"] = result.apply(
        lambda row: safe_div((row.get("saves", 0) or 0) * 1000.0, row.get("views")),
        axis=1,
    )
    result["engagement_rate"] = result.apply(
        lambda row: safe_div(
            (row.get("likes", 0) or 0)
            + (row.get("comments", 0) or 0)
            + (row.get("saves", 0) or 0)
            + (row.get("shares", 0) or 0),
            row.get("views"),
        ),
        axis=1,
    )
    return result


def compute_j_score(df: pd.DataFrame) -> pd.DataFrame:
    cfg = load_metrics_config()
    weights = cfg.get("objective", {}).get(
        "weights",
        {"save_rate": 0.6, "comment_rate": 0.3, "dm_rate": 0.1},
    )
    result = df.copy()
    result["J_score"] = (
        weights.get("save_rate", 0) * result["save_rate"]
        + weights.get("comment_rate", 0) * result["comment_rate"]
        + weights.get("dm_rate", 0) * result["dm_rate"]
    )
    return result
