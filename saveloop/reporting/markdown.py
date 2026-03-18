from __future__ import annotations

from pathlib import Path

import pandas as pd

from saveloop.analysis.recommendations import generate_recommendation
from saveloop.config import load_settings
from saveloop.io.loaders import load_csv_if_exists, load_posts_log
from saveloop.io.writers import ensure_output_dirs, write_dataframe, write_text
from saveloop.metrics.aggregations import aggregate_pattern_performance, aggregate_tag_performance
from saveloop.metrics.core import compute_j_score, compute_rates
from saveloop.metrics.derived import apply_derived_metrics
from saveloop.models.report import WeeklyReport
from saveloop.reporting.weekly_summary import build_weekly_summary


def run_analysis_pipeline() -> dict[str, Path]:
    ensure_output_dirs()
    posts_df = load_posts_log()
    posts_df = compute_rates(posts_df)
    posts_df = compute_j_score(posts_df)
    posts_df = apply_derived_metrics(posts_df)

    tag_performance = aggregate_tag_performance(posts_df)
    pattern_performance = aggregate_pattern_performance(posts_df)

    posts_path = write_dataframe(posts_df, "posts_log_with_metrics.csv")
    tag_path = write_dataframe(tag_performance, "tag_performance.csv")
    pattern_path = write_dataframe(pattern_performance, "pattern_performance.csv")

    return {
        "posts": posts_path,
        "tag_performance": tag_path,
        "pattern_performance": pattern_path,
    }


def write_summary() -> Path:
    outputs = run_analysis_pipeline()
    posts_df = pd.read_csv(outputs["posts"])
    tag_performance = pd.read_csv(outputs["tag_performance"])
    pattern_performance = pd.read_csv(outputs["pattern_performance"])
    _ = load_csv_if_exists("experiments_backlog.csv")

    best_post_id = None
    best_j = None
    highlights: list[str] = []
    if not posts_df["J_score"].dropna().empty:
        best_index = posts_df["J_score"].idxmax()
        best_post_id = str(posts_df.loc[best_index, "post_id"])
        best_j = float(posts_df.loc[best_index, "J_score"])
        highlights.append(f"Best current post is {best_post_id}.")

    wins_count = int((posts_df["win_flag"] == "win").sum()) if "win_flag" in posts_df.columns else 0
    if not tag_performance.empty:
        top_tag = tag_performance.iloc[0]["tag"]
        highlights.append(f"Top current tag by mean J is {top_tag}.")

    report = WeeklyReport(
        posts_analysed=len(posts_df),
        mean_j=float(posts_df["J_score"].mean()) if not posts_df["J_score"].dropna().empty else None,
        best_post_id=best_post_id,
        best_j=best_j,
        wins=wins_count,
        highlights=highlights,
    )
    recommendation = generate_recommendation(posts_df, tag_performance, pattern_performance)

    settings = load_settings()
    filename = settings.get("reporting", {}).get("summary_filename", "weekly_summary.md")
    text = build_weekly_summary(report, recommendation)
    return write_text(text, filename)
