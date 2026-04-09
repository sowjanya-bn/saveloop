from __future__ import annotations

from saveloop.models.experiment import Recommendation
from saveloop.models.report import WeeklyReport


def build_weekly_summary(report: WeeklyReport, recommendation: Recommendation) -> str:
    lines: list[str] = ["# Weekly Summary", ""]

    lines.append("## Overview")
    lines.append(f"- Posts analysed: {report.posts_analysed}")
    if report.mean_j is not None:
        lines.append(f"- Mean J score: {report.mean_j:.4f}")
    if report.best_post_id and report.best_j is not None:
        lines.append(f"- Best current post: {report.best_post_id} ({report.best_j:.4f})")
    lines.append(f"- Wins this week: {report.wins}")

    if report.low_data_warning:
        lines.append("")
        lines.append("## Data confidence")
        lines.append(f"- {report.low_data_warning}")

    if report.highlights:
        lines.append("")
        lines.append("## What worked")
        for highlight in report.highlights:
            lines.append(f"- {highlight}")

    lines.append("")
    lines.append("## Next Recommendation")
    lines.append("- What is working best right now: " + recommendation.top_signal_description)
    lines.append(f"- Why this stands out: {recommendation.reason}")
    lines.append(f"- What to do next: {recommendation.next_action}")
    if recommendation.secondary_action:
        lines.append(f"- Keep in mind: {recommendation.secondary_action}")
    lines.append(f"- Confidence level: {recommendation.confidence_label} ({recommendation.confidence:.2f})")
    if recommendation.evidence_note:
        lines.append(f"- Evidence note: {recommendation.evidence_note}")

    return "\n".join(lines) + "\n"
