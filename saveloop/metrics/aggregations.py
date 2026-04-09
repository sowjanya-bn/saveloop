from __future__ import annotations

import pandas as pd


def _split_tags(tag_text: object) -> list[str]:
    if not isinstance(tag_text, str):
        return []
    return [tag.strip() for tag in tag_text.split(",") if tag.strip()]


def aggregate_tag_performance(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in df.iterrows():
        for tag in _split_tags(row.get("aesthetic_tags")):
            rows.append(
                {
                    "tag": tag,
                    "J_score": row.get("J_score"),
                    "engagement_rate": row.get("engagement_rate"),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["tag", "count", "J_mean", "ER_mean"])
    tag_df = pd.DataFrame(rows)
    return (
        tag_df.groupby("tag")
        .agg(count=("J_score", "count"), J_mean=("J_score", "mean"), ER_mean=("engagement_rate", "mean"))
        .reset_index()
        .sort_values(["J_mean", "count"], ascending=[False, False])
    )


def aggregate_pattern_performance(df: pd.DataFrame) -> pd.DataFrame:
    if "pattern" not in df.columns:
        return pd.DataFrame(columns=["pattern", "count", "J_mean", "ER_mean"])
    return (
        df.groupby("pattern")
        .agg(count=("J_score", "count"), J_mean=("J_score", "mean"), ER_mean=("engagement_rate", "mean"))
        .reset_index()
        .sort_values(["J_mean", "count"], ascending=[False, False])
    )
