from __future__ import annotations

from typing import Any


def _tone_for_theme(theme: str) -> str:
    return {
        "fitness": "clear, energetic, practical",
        "productivity": "calm, helpful, focused",
        "food": "warm, simple, useful",
        "lifestyle": "soft, reflective, relatable",
    }.get(theme, "clear, practical")


def generate_script(bundle: dict[str, Any]) -> dict[str, Any]:
    theme = str(bundle.get("theme", "general"))
    keyword = str(bundle.get("trend_keyword", "this idea"))
    hook = str(bundle.get("hook", f"Why {keyword} is worth trying"))
    caption_stub = str(bundle.get("caption_stub", f"A simple take on {keyword}."))
    cta = str(bundle.get("cta", "Save this for later"))

    bullets = {
        "fitness": [
            f"Show the usual mistake people make with {keyword}",
            "Reveal one easy fix people can try today",
            "End with the practical takeaway worth saving",
        ],
        "productivity": [
            f"Open with the friction point behind {keyword}",
            "Show a realistic routine, not an idealised one",
            "Close with one step the viewer can copy tomorrow",
        ],
        "food": [
            f"Lead with the most useful result tied to {keyword}",
            "Keep the middle section visual and easy to follow",
            "Finish with the one reason this is worth saving",
        ],
        "lifestyle": [
            f"Frame {keyword} as a relatable everyday moment",
            "Keep the pacing gentle and visually grounded",
            "End with a small reflective takeaway people want to revisit",
        ],
    }.get(theme, [
        f"Start with a clear reason {keyword} matters right now",
        "Keep the middle section simple and concrete",
        "End with one memorable takeaway",
    ])

    caption = (
        f"{caption_stub} \n\n"
        f"Try this angle: make the first beat instantly clear, keep the visual language consistent, and finish with a takeaway people will want to save.\n\n"
        f"{cta}."
    )

    overlay_text = hook if len(hook) <= 75 else hook[:72].rstrip() + "..."

    return {
        "tone": _tone_for_theme(theme),
        "hook": hook,
        "overlay_text": overlay_text,
        "caption": caption,
        "bullets": bullets,
        "closing_cta": cta,
    }
