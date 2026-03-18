from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class WeeklyReport:
    posts_analysed: int
    mean_j: float | None
    best_post_id: str | None
    best_j: float | None
    wins: int
    highlights: list[str] = field(default_factory=list)
    suggestion: str | None = None
