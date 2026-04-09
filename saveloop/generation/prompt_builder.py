from __future__ import annotations

from textwrap import dedent
from typing import Any


def build_copy_prompt(bundle: dict[str, Any]) -> str:
    keyword = bundle.get('trend_keyword', '')
    angle = bundle.get('angle', '')
    caption_direction = bundle.get('caption_direction', '')

    return dedent(
        f"""
        You are writing real Instagram carousel content for a UK-based creator
        whose niche is budget-friendly weeknight recipes, simple grocery swaps, and tiny Sunday resets.

        Brand voice: warm, honest, unpretentious — like a friend sharing a genuinely useful tip.
        Aesthetic: warm kitchen light, clean backgrounds, short overlays (maximum 6 words on any slide).
        Optimise for saves: every slide should give the viewer a reason to bookmark this.
        Do not use American spellings. Write in British English.

        Topic: {keyword}
        Angle: {angle}
        What this post should cover: {caption_direction}
        Hook already written: {bundle.get('hook', '')}
        Caption stub: {bundle.get('caption_stub', '')}
        Theme: {bundle.get('theme', '')}
        Format: {bundle.get('format', '')}
        Hook style: {bundle.get('hook_style', '')}
        CTA: {bundle.get('cta', '')}
        Hashtags: {bundle.get('hashtags', '')}

        CRITICAL RULE: Every slide body must contain the ACTUAL information — real tips, real steps,
        real facts about "{keyword}". Do NOT write structural descriptions like "here is how to do X"
        or "this is the step you should take". Write the actual step. Write the real tip.

        Example of BAD slide body: "One ingredient change is usually all it takes."
        Example of GOOD slide body: "Swap branded cereal for own-brand — same nutrition, £1.40 cheaper per box."

        Example of BAD slide body: "Show the usual mistake people make with {keyword}."
        Example of GOOD slide body: "Most people add flavoured protein powder — it goes chalky. Use unflavoured whey or Greek yoghurt instead."

        Viral hook patterns — pick the best fit:
        - question: "Why does {keyword} actually work?"
        - bold_claim: "This is the only {keyword} method worth trying"
        - number_list: "5 things nobody tells you about {keyword}"
        - contrast: "Everyone does {keyword} wrong. Here is what actually works."
        - story_open: "I used to get {keyword} completely wrong until I tried this"

        Return valid JSON only with this exact shape:
        {{
          "tone": "string",
          "hook": "string",
          "hook_pattern": "one of: question | bold_claim | number_list | contrast | story_open",
          "overlay_text": "string",
          "caption": "string",
          "bullets": ["string", "string", "string"],
          "closing_cta": "string",
          "slides": [
            {{"title": "string", "body": "string"}},
            {{"title": "string", "body": "string"}},
            {{"title": "string", "body": "string"}},
            {{"title": "string", "body": "string"}},
            {{"title": "string", "body": "string"}}
          ]
        }}

        Requirements:
        - hook under 95 characters, uses a viral pattern above
        - hook_pattern is exactly one of the five listed values
        - overlay_text under 80 characters
        - caption: 3-5 sentences, natural, save-worthy, written as a human creator would post it
        - slides: exactly 5 items, each body contains the REAL content (specific to "{keyword}"), title under 40 chars, body under 120 chars
        - slide arc: what it is → how to do it → the key detail most people miss → common mistake → save-worthy takeaway
        - bullets: 3 practical beats for a reel script, specific to this topic
        """
    ).strip()
