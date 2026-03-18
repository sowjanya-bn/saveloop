from __future__ import annotations

from saveloop.models.experiment import Recommendation
from saveloop.models.report import WeeklyReport


def build_weekly_summary(report: WeeklyReport, recommendation: Recommendation) -> str:
    lines: list[str] = ["# Weekly Summary", ""]
    lines.append(f"- Posts analysed: {report.posts_analysed}")
    if report.mean_j is not None:
        lines.append(f"- Mean J: {report.mean_j:.4f}")
    if report.best_post_id and report.best_j is not None:
        lines.append(f"- Best J: {report.best_j:.4f} (post: {report.best_post_id})")
    lines.append(f"- Wins this week: {report.wins}")

    if report.highlights:
        lines.append("")
        lines.append("## Highlights")
        for highlight in report.highlights:
            lines.append(f"- {highlight}")

    lines.append("")
    lines.append("## Next Recommendation")
    lines.append(f"- Top signal: {recommendation.top_signal}")
    lines.append(f"- Confidence: {recommendation.confidence:.2f}")
    lines.append(f"- Why: {recommendation.reason}")
    lines.append(f"- Next action: {recommendation.next_action}")
    if recommendation.secondary_action:
        lines.append(f"- Secondary action: {recommendation.secondary_action}")

    return "\n".join(lines) + "\n"
