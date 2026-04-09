from __future__ import annotations

import hashlib

import pandas as pd


# ── Content pillars ───────────────────────────────────────────────────────────
# Three pillars: weeknight_recipes | grocery_swaps | sunday_reset
# Detection is keyword-based; fallback to generic food/lifestyle handling.

_SWAP_SIGNALS = {"swap", "dupe", "own-brand", "branded", "alternative", "switch", "instead"}
_RESET_SIGNALS = {"sunday", "reset", "ritual", "habit", "checklist", "routine", "weekly"}
_RECIPE_SIGNALS = {"dinner", "meal", "recipe", "pan", "cook", "prep", "plan", "eat", "food", "cheap", "budget", "£"}


def _detect_pillar(keyword: str) -> str:
    kw = keyword.lower()
    if any(s in kw for s in _SWAP_SIGNALS):
        return "grocery_swaps"
    if any(s in kw for s in _RESET_SIGNALS):
        return "sunday_reset"
    if any(s in kw for s in _RECIPE_SIGNALS):
        return "weeknight_recipes"
    return "general"


# ── Pillar configs ────────────────────────────────────────────────────────────

_PILLAR = {
    "weeknight_recipes": {
        "format": "carousel",
        "hook_style": "utility_first",
        "aesthetic_tags": "warm_minimal,kitchen_closeup",
        "visual_direction": "Warm overhead kitchen light, ingredients laid flat, short text overlay maximum 6 words, no clutter",
        "posting_window": "17:00-19:00",
        "cta": "Save this for tonight",
        "hashtags": "#BudgetMeals,#WeeknightDinner,#CheapEats,#MealIdeas,#BudgetCooking,#EasyDinner,#FamilyMeals",
        "angle_template": "A real under-{price} weeknight dinner that takes under 20 minutes and actually tastes good",
        "caption_direction_template": "Show the finished dish first, list the key ingredients and rough cost, give one tip that makes it easier, end with the save CTA.",
    },
    "grocery_swaps": {
        "format": "carousel",
        "hook_style": "utility_first",
        "aesthetic_tags": "warm_minimal,flat_lay,high_contrast",
        "visual_direction": "Side-by-side flat lay of branded vs own-brand items, warm light, short bold overlay showing the saving",
        "posting_window": "10:00-12:00",
        "cta": "Save this before your next shop",
        "hashtags": "#GrocerySwaps,#SaveMoney,#BudgetShopping,#SupermarketHacks,#GroceryHaul,#MoneySaving,#OwnBrand",
        "angle_template": "Simple swaps that cut the weekly shop without changing what you eat",
        "caption_direction_template": "Lead with the total saving, list each swap with exact price difference, end with the save CTA. Keep it scannable.",
    },
    "sunday_reset": {
        "format": "carousel",
        "hook_style": "story_first",
        "aesthetic_tags": "warm_minimal,soft_light,home_corner",
        "visual_direction": "Soft Sunday morning light, calm home corner, minimal props, short overlay maximum 5 words",
        "posting_window": "08:00-10:00",
        "cta": "Save this for Sunday",
        "hashtags": "#SundayReset,#SundayRoutine,#WeeklyReset,#SundayVibes,#SlowSunday,#ResetDay,#SundayHabits",
        "angle_template": "A tiny doable Sunday reset that makes the week feel manageable — not aspirational, just honest",
        "caption_direction_template": "Start with the feeling (not the aesthetic), share 3-5 small specific actions, end with why it works, then the save CTA.",
    },
    "general": {
        "format": "carousel",
        "hook_style": "utility_first",
        "aesthetic_tags": "warm_minimal,close_up",
        "visual_direction": "Warm light, clean background, short text overlay",
        "posting_window": "18:00-20:00",
        "cta": "Save this for later",
        "hashtags": "#SaveMoney,#BudgetTips,#SimpleLife,#MoneySaving",
        "angle_template": "A practical, honest take on {keyword} that is actually worth saving",
        "caption_direction_template": "Lead with the most useful point, keep it specific, end with the save CTA.",
    },
}

_PRICE_BY_KEYWORD = {
    "£3": "£3",
    "£5": "£5",
    "£30": "£30",
}


def _price_hint(keyword: str) -> str:
    for token, price in _PRICE_BY_KEYWORD.items():
        if token in keyword:
            return price
    return "£3–5"


def _hook(keyword: str, pillar: str) -> str:
    hooks = {
        "grocery_swaps": f"These grocery swaps could save you £20 this week",
        "sunday_reset": f"My tiny Sunday reset — takes 30 minutes and fixes the whole week",
        "weeknight_recipes": f"A {_price_hint(keyword)} weeknight dinner that actually tastes good",
        "general": f"The simplest version of {keyword} — and it works",
    }
    return hooks.get(pillar, f"Why {keyword} is worth knowing")


def _angle(keyword: str, pillar: str) -> str:
    template = _PILLAR[pillar]["angle_template"]
    return template.replace("{keyword}", keyword).replace("{price}", _price_hint(keyword))


def _caption_direction(keyword: str, pillar: str) -> str:
    return _PILLAR[pillar]["caption_direction_template"]


def _caption_stub(keyword: str, pillar: str) -> str:
    stubs = {
        "grocery_swaps": f"I switched to own-brand on these and honestly could not tell the difference.",
        "sunday_reset": f"Sunday does not have to be productive. It just has to feel reset.",
        "weeknight_recipes": f"This is what I make when I need dinner fast and do not want to think about it.",
        "general": f"Here is the simple version of {keyword} that is actually worth saving.",
    }
    return stubs.get(pillar, f"A simple take on {keyword}.")


def _bundle_title(keyword: str, pillar: str) -> str:
    titles = {
        "grocery_swaps": keyword.title(),
        "sunday_reset": keyword.title(),
        "weeknight_recipes": keyword.title(),
        "general": keyword.title(),
    }
    return titles.get(pillar, keyword.title())


def _bundle_id(keyword: str, theme: str) -> str:
    text = f"{theme}:{keyword}".encode("utf-8")
    return hashlib.md5(text).hexdigest()[:8]


def generate_bundles(trends_df: pd.DataFrame) -> pd.DataFrame:
    bundles: list[dict[str, object]] = []

    for _, row in trends_df.iterrows():
        keyword = str(row["keyword"]).strip()
        theme = str(row["theme"]).strip() or "general"
        momentum = float(row.get("trend_score", row.get("momentum_score", 0.0)) or 0.0)
        pillar = _detect_pillar(keyword)
        cfg = _PILLAR[pillar]

        bundles.append({
            "bundle_id": _bundle_id(keyword, theme),
            "bundle_title": _bundle_title(keyword, pillar),
            "trend_keyword": keyword,
            "theme": theme,
            "pillar": pillar,
            "angle": _angle(keyword, pillar),
            "format": cfg["format"],
            "hook_style": cfg["hook_style"],
            "hook": _hook(keyword, pillar),
            "caption_direction": _caption_direction(keyword, pillar),
            "caption_stub": _caption_stub(keyword, pillar),
            "visual_direction": cfg["visual_direction"],
            "aesthetic_tags": cfg["aesthetic_tags"],
            "posting_window": cfg["posting_window"],
            "cta": cfg["cta"],
            "hashtags": cfg["hashtags"],
            "priority_score": round(momentum, 3),
            "status": "draft",
            "notes": row.get("notes", ""),
        })

    bundles_df = pd.DataFrame(bundles)
    if bundles_df.empty:
        return bundles_df
    return bundles_df.sort_values(["priority_score", "trend_keyword"], ascending=[False, True]).reset_index(drop=True)
