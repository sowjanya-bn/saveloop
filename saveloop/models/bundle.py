from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContentBundle:
    bundle_id: str
    bundle_title: str
    trend_keyword: str
    theme: str
    angle: str
    format: str
    hook_style: str
    hook: str
    caption_direction: str
    caption_stub: str
    visual_direction: str
    aesthetic_tags: str
    posting_window: str
    cta: str
    hashtags: str
    priority_score: float
    status: str = "draft"
    notes: str = ""
