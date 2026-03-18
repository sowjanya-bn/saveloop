from __future__ import annotations

import pandas as pd

from saveloop.analysis.pattern_analysis import best_pattern
from saveloop.analysis.tag_analysis import best_tag
from saveloop.config import load_experiments_config
from saveloop.models.experiment import Recommendation


def generate_recommendation(
    posts_df: pd.DataFrame,
    tag_performance: pd.DataFrame,
    pattern_performance: pd.DataFrame,
) -> Recommendation:
    cfg = load_experiments_config()
    min_observations = cfg.get("strategy", {}).get("min_observations_for_confidence", 2)
    wins = posts_df[posts_df["win_flag"] == "win"] if "win_flag" in posts_df.columns else pd.DataFrame()

    tag = best_tag(tag_performance, min_count=min_observations)
    pattern = best_pattern(pattern_performance)

    if tag is not None:
        confidence = min(0.95, 0.5 + 0.1 * float(tag["count"]))
        secondary_action = None
        if wins.empty:
            secondary_action = "Shift posting time by plus or minus 60 minutes while keeping one control post."
        return Recommendation(
            top_signal=str(tag["tag"]),
            confidence=confidence,
            reason=f"Highest mean J across {int(tag['count'])} tagged posts.",
            next_action=f"Keep {tag['tag']} and test steam first vs text first on the next reel.",
            secondary_action=secondary_action,
        )

    if pattern is not None:
        return Recommendation(
            top_signal=str(pattern["pattern"]),
            confidence=0.55,
            reason="Strongest current pattern based on mean J.",
            next_action=f"Use pattern {pattern['pattern']} again and vary only one aesthetic lever.",
            secondary_action="Keep one control post unchanged for a cleaner comparison.",
        )

    return Recommendation(
        top_signal="control",
        confidence=0.4,
        reason="Not enough data yet for a stronger signal.",
        next_action="Keep one control post and test one aesthetic lever plus one timing lever next week.",
        secondary_action="Log complete data for each post so confidence can improve.",
    )
