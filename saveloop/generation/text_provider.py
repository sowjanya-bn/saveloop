from __future__ import annotations

import json
import os
from typing import Any

from saveloop.generation.prompt_builder import build_copy_prompt
from saveloop.generation.script_generator import generate_script


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    return json.loads(text[start:end + 1])


_ALLOWED_HOOK_PATTERNS = {"question", "bold_claim", "number_list", "contrast", "story_open"}


def _normalize_copy(data: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    bullets = data.get("bullets") or fallback["bullets"]
    if not isinstance(bullets, list):
        bullets = fallback["bullets"]

    hook = str(data.get("hook") or fallback["hook"]).strip()
    overlay = str(data.get("overlay_text") or hook).strip()
    if len(overlay) > 80:
        overlay = overlay[:77].rstrip() + "..."

    normalized_bullets = [str(b).strip() for b in bullets if str(b).strip()]
    if len(normalized_bullets) < 3:
        normalized_bullets = fallback["bullets"]

    # slides — must be exactly 5 {"title": str, "body": str} dicts
    raw_slides = data.get("slides") or []
    valid_slides: list[dict[str, str]] = []
    if isinstance(raw_slides, list):
        for s in raw_slides:
            if isinstance(s, dict) and s.get("title") and s.get("body"):
                valid_slides.append({
                    "title": str(s["title"]).strip()[:40],
                    "body": str(s["body"]).strip()[:120],
                })
    if len(valid_slides) != 5:
        valid_slides = fallback.get("slides", [])

    # hook_pattern
    hook_pattern = str(data.get("hook_pattern") or fallback.get("hook_pattern", "bold_claim")).strip()
    if hook_pattern not in _ALLOWED_HOOK_PATTERNS:
        hook_pattern = fallback.get("hook_pattern", "bold_claim")

    return {
        "tone": str(data.get("tone") or fallback["tone"]).strip(),
        "hook": hook,
        "overlay_text": overlay,
        "caption": str(data.get("caption") or fallback["caption"]).strip(),
        "bullets": normalized_bullets[:3],
        "closing_cta": str(data.get("closing_cta") or fallback["closing_cta"]).strip(),
        "hook_pattern": hook_pattern,
        "slides": valid_slides,
    }


def _call_gemini_model(prompt: str, api_key: str, model_name: str) -> str:
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return getattr(response, "text", "") or ""


def _gemini_generate(bundle: dict[str, Any], model: str | None = None) -> dict[str, Any]:
    fallback = generate_script(bundle)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback

    try:
        import google.genai  # noqa: F401
    except Exception:
        return fallback

    model_name = model or os.getenv("SAVELOOP_TEXT_MODEL", "gemini-3-flash-preview")
    prompt = build_copy_prompt(bundle)

    try:
        text = _call_gemini_model(prompt, api_key, model_name)
        if not text:
            return fallback
        parsed = _extract_json(text)
        return _normalize_copy(parsed, fallback)
    except Exception:
        fallback_model = os.getenv("SAVELOOP_TEXT_FALLBACK_MODEL", "gemini-3.1-flash-lite-preview")
        if fallback_model and fallback_model != model_name:
            try:
                text = _call_gemini_model(prompt, api_key, fallback_model)
                if text:
                    parsed = _extract_json(text)
                    normalized = _normalize_copy(parsed, fallback)
                    normalized["tone"] = f"{normalized['tone']} (fallback:{fallback_model})"
                    return normalized
            except Exception:
                return fallback
        return fallback


def generate_post_copy(bundle: dict[str, Any], provider: str = "rule_based") -> dict[str, Any]:
    if provider == "gemini":
        return _gemini_generate(bundle)
    return generate_script(bundle)
