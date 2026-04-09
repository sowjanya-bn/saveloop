from __future__ import annotations

import pandas as pd

from saveloop.analysis.pattern_analysis import best_pattern
from saveloop.analysis.tag_analysis import best_tag
from saveloop.config import load_experiments_config
from saveloop.models.experiment import Recommendation

PATTERN_MAP = {
    "P01": "Close-up minimal aesthetic reels",
    "P02": "Text-first hook reels",
    "P03": "Story-led carousel breakdowns",
}


def _confidence_label(score: float) -> str:
    if score < 0.4:
        return "low"
    if score < 0.7:
        return "medium"
    return "high"


def generate_recommendation(
    posts_df: pd.DataFrame,
    tag_performance: pd.DataFrame,
    pattern_performance: pd.DataFrame,
) -> Recommendation:
    cfg = load_experiments_config()
    min_observations = cfg.get("strategy", {}).get("min_observations_for_confidence", 2)
    wins = posts_df[posts_df["win_flag"] == "win"] if "win_flag" in posts_df.columns else pd.DataFrame()

    post_count = len(posts_df)
    low_data_note = None
    if post_count < 5:
        low_data_note = "Evidence is still light, so treat this as a directional nudge rather than a settled rule."

    tag = best_tag(tag_performance, min_count=min_observations)
    pattern = best_pattern(pattern_performance)

    if tag is not None:
        confidence = min(0.95, 0.48 + 0.08 * float(tag["count"]))
        confidence_label = _confidence_label(confidence)
        secondary_action = "Keep one control post unchanged so you can compare the hook cleanly."
        if wins.empty:
            secondary_action = "Keep one control post unchanged and shift posting time by about an hour only after the creative test."
        return Recommendation(
            top_signal=str(tag["tag"]),
            top_signal_description=f"Posts using the {tag['tag']} aesthetic tag",
            confidence=confidence,
            confidence_label=confidence_label,
            reason=f"This tag has the strongest average J score across {int(tag['count'])} observed posts.",
            next_action=f"Build the next post around {tag['tag']} again, but change only the opening hook so you learn what actually moved performance.",
            secondary_action=secondary_action,
            evidence_note=low_data_note,
        )

    if pattern is not None:
        pattern_code = str(pattern["pattern"])
        description = PATTERN_MAP.get(pattern_code, pattern_code)
        confidence = 0.55 if post_count < 5 else 0.68
        return Recommendation(
            top_signal=pattern_code,
            top_signal_description=description,
            confidence=confidence,
            confidence_label=_confidence_label(confidence),
            reason="This pattern is the strongest current performer based on average J score.",
            next_action=f"Use {description.lower()} again and vary only one lever, ideally the first two seconds of the hook.",
            secondary_action="Keep one post visually stable as a control so the next comparison stays clean.",
            evidence_note=low_data_note,
        )

    return Recommendation(
        top_signal="control",
        top_signal_description="No reliable creative signal yet",
        confidence=0.35,
        confidence_label="low",
        reason="There is not enough complete post data yet to call a clear winner.",
        next_action="Post one control piece and one variation next, then log every metric so the system has something real to compare.",
        secondary_action="Avoid changing multiple creative choices at once.",
        evidence_note=low_data_note,
    )
