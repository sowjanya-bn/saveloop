from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Candidate:
    candidate_id: str
    source: str                         # reddit/r/X | rss/which | submission | manual
    raw_text: str                        # original text or submission content
    theme: str                           # shrinkflation | fake_deals | single_person | subscriptions | honest_meal | reddit | community
    product: Optional[str] = None
    retailer: Optional[str] = None
    claimed_change: Optional[str] = None   # "box reduced from 400g to 350g"
    old_value: Optional[str] = None        # price or size before
    new_value: Optional[str] = None        # price or size after
    unit_price_before: Optional[float] = None
    unit_price_after: Optional[float] = None
    verified_increase_pct: Optional[float] = None
    source_url: Optional[str] = None
    submitted_by: Optional[str] = None     # anonymous token for community submissions
    observed_at: str = field(default_factory=lambda: date.today().isoformat())

    # Verification workflow
    status: str = "new"
    # new | pending_review | verified | needs_more_evidence | rejected | duplicate | posted

    verification_label: str = "unverified"
    # verified | reader_submitted_checking | interesting_unconfirmed | unverified

    verification_notes: str = ""
    confidence: float = 0.0   # 0.0–1.0, set during verification
