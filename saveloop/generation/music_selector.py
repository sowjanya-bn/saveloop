from __future__ import annotations

from typing import Any


def select_music(bundle: dict[str, Any]) -> dict[str, str]:
    theme = str(bundle.get("theme", "general"))
    hook_style = str(bundle.get("hook_style", "curiosity_first"))

    by_theme = {
        "fitness": ("Upbeat training pop", "steady build, clean drop, motivating but not aggressive"),
        "productivity": ("Focused lo-fi groove", "soft percussion, warm keys, morning energy"),
        "food": ("Light lifestyle acoustic", "bright, simple, friendly, easy under voiceover"),
        "lifestyle": ("Gentle cinematic chill", "soft rise, reflective tone, day-in-the-life pacing"),
    }
    genre, note = by_theme.get(theme, ("Modern creator background track", "clean and unobtrusive"))

    emphasis = {
        "problem_first": "Start right on the beat so the opening friction lands quickly.",
        "curiosity_first": "Use a softer intro so the hook text carries the first beat.",
        "utility_first": "Pick something light that leaves room for step-by-step text.",
        "story_first": "Choose a gentle intro and let the track build behind the narrative.",
    }.get(hook_style, "Keep the intro clean so the hook remains readable.")

    return {
        "music_style": genre,
        "music_note": f"{note}. {emphasis}",
    }
