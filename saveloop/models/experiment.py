from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Recommendation:
    top_signal: str
    confidence: float
    reason: str
    next_action: str
    secondary_action: str | None = None
