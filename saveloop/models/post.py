from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class PostRecord:
    post_id: str
    date_posted: Optional[str] = None
    format: Optional[str] = None
    pattern: Optional[str] = None
    aesthetic_tags: Optional[str] = None
    views: Optional[float] = None
    reach: Optional[float] = None
    likes: Optional[float] = None
    comments: Optional[float] = None
    saves: Optional[float] = None
    shares: Optional[float] = None
    profile_visits: Optional[float] = None
    follows: Optional[float] = None
    avg_view_duration_s: Optional[float] = None
    replays: Optional[float] = None
    dms_started: Optional[float] = None
    note: Optional[str] = None
