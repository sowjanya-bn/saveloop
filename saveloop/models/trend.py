from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrendSignal:
    source: str
    theme: str
    keyword: str
    momentum_score: float | None
    observed_at: str
    notes: str | None = None
