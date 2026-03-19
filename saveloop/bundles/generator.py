from __future__ import annotations

import hashlib

import pandas as pd


FORMAT_BY_THEME = {
    "fitness": "reel",
    "productivity": "reel",
    "food": "carousel",
    "lifestyle": "reel",
}

AESTHETIC_BY_THEME = {
    "fitness": "clean_bright,close_up",
    "productivity": "warm_minimal,desk_setup",
    "food": "warm_minimal,kitchen_close_up",
    "lifestyle": "soft_light,day_in_life",
}

VISUAL_BY_THEME = {
    "fitness": "Bright kitchen counter, quick cut sequence, simple overlay text",
    "productivity": "Desk setup, calm morning light, minimal movement",
    "food": "Ingredient close-ups, warm tones, step-by-step slides",
    "lifestyle": "Soft daylight, candid routine shots, gentle pacing",
}

HOOK_STYLE_BY_THEME = {
    "fitness": "problem_first",
    "productivity": "curiosity_first",
    "food": "utility_first",
    "lifestyle": "story_first",
}

CTA_BY_THEME = {
    "fitness": "Save this for your next workout week",
    "productivity": "Save this for your next planning session",
    "food": "Save this for your next grocery run",
    "lifestyle": "Save this for your next reset day",
}

POSTING_WINDOW_BY_THEME = {
    "fitness": "07:00-09:00",
    "productivity": "07:30-09:30",
    "food": "11:00-13:00",
    "lifestyle": "18:00-20:00",
}


def _bundle_id(keyword: str, theme: str) -> str:
    text = f"{theme}:{keyword}".encode("utf-8")
    return hashlib.md5(text).hexdigest()[:8]


def _hashtags(keyword: str, theme: str) -> str:
    safe_keyword = "".join(part.capitalize() for part in keyword.split())
    safe_theme = "".join(part.capitalize() for part in theme.split())
    return f"#{safe_keyword},#{safe_theme},#contentstrategy,#creatorworkflow"


def _bundle_title(keyword: str, theme: str) -> str:
    return f"{theme.title()} angle: {keyword.title()}"


def generate_bundles(trends_df: pd.DataFrame) -> pd.DataFrame:
    bundles: list[dict[str, object]] = []

    for _, row in trends_df.iterrows():
        keyword = str(row["keyword"]).strip()
        theme = str(row["theme"]).strip() or "general"
        momentum = float(row.get("trend_score", row.get("momentum_score", 0.0)) or 0.0)
        post_format = FORMAT_BY_THEME.get(theme, "reel")
        aesthetic = AESTHETIC_BY_THEME.get(theme, "warm_minimal,close_up")
        cta = CTA_BY_THEME.get(theme, "Save this for later")

        bundles.append(
            {
                "bundle_id": _bundle_id(keyword, theme),
                "bundle_title": _bundle_title(keyword, theme),
                "trend_keyword": keyword,
                "theme": theme,
                "angle": f"A practical creator-friendly take on {keyword}",
                "format": post_format,
                "hook_style": HOOK_STYLE_BY_THEME.get(theme, "curiosity_first"),
                "hook": f"Why {keyword} is everywhere right now and how to make it useful",
                "caption_direction": f"Explain the trend, show one simple use case, and end with a clear takeaway about {keyword}.",
                "caption_stub": f"Everyone is talking about {keyword}. Here is the simple version worth trying.",
                "visual_direction": VISUAL_BY_THEME.get(theme, "Clean close-up shots with simple pacing"),
                "aesthetic_tags": aesthetic,
                "posting_window": POSTING_WINDOW_BY_THEME.get(theme, "18:00-20:00"),
                "cta": cta,
                "hashtags": _hashtags(keyword, theme),
                "priority_score": round(momentum, 3),
                "status": "draft",
                "notes": row.get("notes", ""),
            }
        )

    bundles_df = pd.DataFrame(bundles)
    if bundles_df.empty:
        return bundles_df
    return bundles_df.sort_values(["priority_score", "trend_keyword"], ascending=[False, True]).reset_index(drop=True)
