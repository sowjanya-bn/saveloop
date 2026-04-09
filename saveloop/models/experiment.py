from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Recommendation:
    top_signal: str
    top_signal_description: str
    confidence: float
    confidence_label: str
    reason: str
    next_action: str
    secondary_action: str | None = None
    evidence_note: str | None = None
