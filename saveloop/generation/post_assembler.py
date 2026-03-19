from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from saveloop.generation.image_provider import maybe_generate_image
from saveloop.generation.music_selector import select_music
from saveloop.generation.text_provider import generate_post_copy

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "post_plans.json"


def build_post_plan(
    bundle: dict[str, Any],
    text_provider: str = "rule_based",
    generate_image_asset: bool = False,
) -> dict[str, Any]:
    copy = generate_post_copy(bundle, provider=text_provider)
    image = maybe_generate_image(bundle, copy, generate_asset=generate_image_asset)
    music = select_music(bundle)

    return {
        "bundle_id": bundle.get("bundle_id"),
        "bundle_title": bundle.get("bundle_title"),
        "trend_keyword": bundle.get("trend_keyword"),
        "theme": bundle.get("theme"),
        "format": bundle.get("format"),
        "posting_window": bundle.get("posting_window"),
        "priority_score": bundle.get("priority_score"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "text_provider": text_provider,
        "hook": copy["hook"],
        "overlay_text": copy["overlay_text"],
        "caption": copy["caption"],
        "script_bullets": copy["bullets"],
        "tone": copy["tone"],
        "closing_cta": copy["closing_cta"],
        "image_prompt": image["image_prompt"],
        "image_alt_text": image["alt_text"],
        "image_path": image.get("image_path"),
        "image_generated": image.get("image_generated", False),
        "image_backend": image.get("image_backend"),
        "image_error": image.get("image_error"),
        "music_style": music["music_style"],
        "music_note": music["music_note"],
        "hashtags": bundle.get("hashtags"),
        "status": "generated",
    }


def save_post_plan(plan: dict[str, Any], output_path: Path | None = None) -> Path:
    path = output_path or DEFAULT_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: list[dict[str, Any]] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except json.JSONDecodeError:
            existing = []

    existing = [item for item in existing if item.get("bundle_id") != plan.get("bundle_id")]
    existing.append(plan)
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
