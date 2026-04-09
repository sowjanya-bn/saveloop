from __future__ import annotations

from typing import Any


def generate_image_prompt(bundle: dict[str, Any]) -> dict[str, str]:
    keyword = str(bundle.get("trend_keyword", "content trend"))
    theme = str(bundle.get("theme", "general"))
    visual_direction = str(bundle.get("visual_direction", "Clean close-up shots with simple pacing"))
    aesthetic_tags = str(bundle.get("aesthetic_tags", "warm_minimal,close_up")).replace(",", ", ")

    prompt = (
        f"Instagram {bundle.get('format', 'post')} concept about {keyword}, theme {theme}. "
        f"Visual direction: {visual_direction}. "
        f"Aesthetic tags: {aesthetic_tags}. "
        f"Editorial, high detail, creator-friendly, natural lighting, text-safe composition."
    )

    return {
        "image_prompt": prompt,
        "alt_text": f"Generated concept image for {keyword} in a {theme} style.",
    }
