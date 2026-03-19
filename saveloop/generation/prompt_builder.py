from __future__ import annotations

from textwrap import dedent
from typing import Any


def build_copy_prompt(bundle: dict[str, Any]) -> str:
    return dedent(
        f"""
        You are writing a short Instagram post kit for a creator workflow tool.

        Bundle context:
        - Title: {bundle.get('bundle_title', '')}
        - Theme: {bundle.get('theme', '')}
        - Trend keyword: {bundle.get('trend_keyword', '')}
        - Format: {bundle.get('format', '')}
        - Hook style: {bundle.get('hook_style', '')}
        - Angle: {bundle.get('angle', '')}
        - Caption direction: {bundle.get('caption_direction', '')}
        - Visual direction: {bundle.get('visual_direction', '')}
        - Aesthetic tags: {bundle.get('aesthetic_tags', '')}
        - CTA: {bundle.get('cta', '')}
        - Hashtags: {bundle.get('hashtags', '')}

        Return valid JSON only with this exact shape:
        {{
          "tone": "string",
          "hook": "string",
          "overlay_text": "string",
          "caption": "string",
          "bullets": ["string", "string", "string"],
          "closing_cta": "string"
        }}

        Requirements:
        - Keep the hook under 95 characters
        - Keep overlay text under 80 characters
        - Make the caption natural, specific, and save-worthy
        - Make the bullets practical and suitable for a reel or carousel beat structure
        - Keep the tone aligned with the theme and visual direction
        """
    ).strip()
