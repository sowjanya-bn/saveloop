from __future__ import annotations

import hashlib

import pandas as pd


# ── Theme → Pillar mapping ────────────────────────────────────────────────────

THEME_TO_PILLAR: dict[str, str] = {
    "shrinkflation": "shrinkflation_watch",
    "fake_deals":    "fake_deal_forensics",
    "single_person": "single_person_tax",
    "subscriptions": "subscription_trap",
    "honest_meal":   "honest_meal_cost",
    "reddit":        "reddit_verified",
    "community":     "saveloop_flag",
}


def _detect_pillar(theme: str) -> str:
    return THEME_TO_PILLAR.get(theme.lower().strip(), "honest_meal_cost")


# ── Pillar configs ────────────────────────────────────────────────────────────

_PILLAR: dict[str, dict] = {
    "shrinkflation_watch": {
        "format": "carousel",
        "hook_style": "outrage_reveal",
        "aesthetic_tags": "product_closeup,high_contrast,before_after",
        "visual_direction": "Side-by-side old vs new packaging, unit price overlay, stark comparison",
        "posting_window": "10:00-12:00",
        "cta": "Save this before your next shop",
        "hashtags": "#Shrinkflation,#UKShopping,#ConsumerRights,#SupermarketTricks,#SaveMoney,#PriceWatch,#ShrinkflationUK",
        "angle_template": "Your {product} did not get more expensive. It got smaller. Here is the proof.",
        "caption_direction_template": "Lead with the size change and exact unit price increase. Name the retailer. End with the practical alternative and save CTA.",
        "verification_required": True,
    },
    "fake_deal_forensics": {
        "format": "carousel",
        "hook_style": "forensic_reveal",
        "aesthetic_tags": "product_closeup,high_contrast,numbers_overlay",
        "visual_direction": "Price tag close-up, unit price calculation shown clearly, bold number overlay",
        "posting_window": "10:00-12:00",
        "cta": "Save this. Check before you buy.",
        "hashtags": "#FakeDeal,#SupermarketTricks,#UnitPrice,#SaveMoney,#ConsumerRights,#GroceryHacks,#PriceCheck",
        "angle_template": "The {deal} sounds like a saving. The unit price says otherwise.",
        "caption_direction_template": "Show the claimed deal, then the actual unit price maths. Name the retailer. One sentence on what to do instead.",
        "verification_required": True,
    },
    "single_person_tax": {
        "format": "reel",
        "hook_style": "empathy_reveal",
        "aesthetic_tags": "kitchen_closeup,warm_light,honest",
        "visual_direction": "Single portion cooking, waste shown honestly, calm warm light",
        "posting_window": "18:00-20:00",
        "cta": "Save this if you cook for one",
        "hashtags": "#CookingForOne,#SinglePersonTax,#BudgetLiving,#SaveMoney,#SoloLiving,#HonestBudget,#StudentLife",
        "angle_template": "The bulk buy is cheaper per gram. But you will bin half of it. Here is the honest maths.",
        "caption_direction_template": "State the bulk buy saving, then show the waste cost. Give the real per-use figure. One honest alternative.",
        "verification_required": True,
    },
    "subscription_trap": {
        "format": "reel",
        "hook_style": "break_even_reveal",
        "aesthetic_tags": "screen_closeup,high_contrast,numbers_overlay",
        "visual_direction": "Phone screen showing subscription, clean overlay with break-even calculation",
        "posting_window": "12:00-14:00",
        "cta": "Save this. Check if yours pays off.",
        "hashtags": "#SubscriptionTrap,#SaveMoney,#HiddenCosts,#BudgetTips,#MoneyLeaks,#CancelCulture,#ConsumerTips",
        "angle_template": "{service} pays off at {threshold} uses per month. Are you hitting that?",
        "caption_direction_template": "State the monthly cost. Show the break-even usage. Give the honest verdict for light vs heavy users.",
        "verification_required": True,
    },
    "honest_meal_cost": {
        "format": "reel",
        "hook_style": "utility_honest",
        "aesthetic_tags": "kitchen_closeup,warm_light,ingredients_flat",
        "visual_direction": "Ingredients laid flat with pro-rata cost labels, warm overhead light, honest total shown",
        "posting_window": "17:00-19:00",
        "cta": "Save this. This is what it actually costs.",
        "hashtags": "#HonestMealCost,#BudgetCooking,#RealCost,#MealPrep,#StudentMeals,#CheapEats,#ActualCost",
        "angle_template": "This {meal} costs {price}. Including the oil, the spices and the gas.",
        "caption_direction_template": "List every ingredient with pro-rata cost included. Show the honest total. No hidden pantry assumptions.",
        "verification_required": False,
    },
    "reddit_verified": {
        "format": "reel",
        "hook_style": "story_lesson",
        "aesthetic_tags": "text_minimal,warm_light,clean_bg",
        "visual_direction": "Clean text overlay on calm background, story-led pacing, lesson card at end",
        "posting_window": "18:00-20:00",
        "cta": "Save this. We checked the numbers.",
        "hashtags": "#MoneyLeaks,#ConsumerTips,#SaveMoney,#RealTalk,#BudgetLife,#VerifiedSaving,#UKMoney",
        "angle_template": "Someone flagged this. We checked the numbers. Here is what we found.",
        "caption_direction_template": "Composite story (never reproduce original post). State the money leak. Show the verified calculation. End with the SaveLoop lesson.",
        "verification_required": True,
    },
    "saveloop_flag": {
        "format": "carousel",
        "hook_style": "community_reveal",
        "aesthetic_tags": "product_closeup,high_contrast,verified_badge",
        "visual_direction": "Submitted photo or product recreation, verified stamp overlay, maths shown clearly",
        "posting_window": "10:00-12:00",
        "cta": "Spot something? Submit it. Link in bio.",
        "hashtags": "#SaveLoopFlag,#Shrinkflation,#ConsumerRights,#SpotIt,#VerifiedSaving,#UKShopping,#MoneyLeaks",
        "angle_template": "A SaveLoop reader spotted this. We checked it. It is real.",
        "caption_direction_template": "Credit the submitter (anonymous unless permission given). State the claim. Show the verification. Give the practical alternative.",
        "verification_required": True,
    },
}


# ── Bundle field builders ─────────────────────────────────────────────────────

def _hook(candidate: dict, pillar: str) -> str:
    product = str(candidate.get("product") or "").strip()
    retailer = str(candidate.get("retailer") or "").strip()
    hooks = {
        "shrinkflation_watch": f"Your {product or 'favourite product'} got smaller. The price did not.",
        "fake_deal_forensics": f"This deal at {retailer or 'the supermarket'} does not add up.",
        "single_person_tax":   "The bulk buy is cheaper per gram. But you will bin half of it.",
        "subscription_trap":   "This subscription pays off at a specific usage level. Are you hitting it?",
        "honest_meal_cost":    f"Here is what {product or 'this meal'} actually costs. Including everything.",
        "reddit_verified":     "Someone flagged this. We checked the numbers. Here is what we found.",
        "saveloop_flag":       "A SaveLoop reader spotted this. We checked it. It is real.",
    }
    return hooks.get(pillar, f"Here is what you need to know about {product or 'this'}.")


def _angle(candidate: dict, pillar: str) -> str:
    template = _PILLAR[pillar]["angle_template"]
    product  = str(candidate.get("product") or "this product")
    deal     = str(candidate.get("claimed_change") or "this deal")
    service  = str(candidate.get("product") or "this subscription")
    meal     = str(candidate.get("product") or "this meal")
    price    = str(candidate.get("new_value") or "?")
    threshold = str(candidate.get("unit_price_after") or "X")
    return (
        template
        .replace("{product}", product)
        .replace("{deal}", deal)
        .replace("{service}", service)
        .replace("{meal}", meal)
        .replace("{price}", price)
        .replace("{threshold}", threshold)
    )


def _caption_direction(pillar: str) -> str:
    return _PILLAR[pillar]["caption_direction_template"]


def _caption_stub(candidate: dict, pillar: str) -> str:
    product  = str(candidate.get("product") or "this product")
    retailer = str(candidate.get("retailer") or "the supermarket")
    stubs = {
        "shrinkflation_watch": f"{product} at {retailer} — same price, less product. Here is the proof.",
        "fake_deal_forensics": "The numbers on this deal do not hold up. Here is the unit price reality.",
        "single_person_tax":   "Buying in bulk sounds smart. For one person, it often is not.",
        "subscription_trap":   "The break-even calculation on this one might surprise you.",
        "honest_meal_cost":    f"This is what {product} actually costs — including the parts recipes leave out.",
        "reddit_verified":     "A reader flagged this. We ran the numbers. Here is the honest verdict.",
        "saveloop_flag":       "Submitted by a SaveLoop reader. Verified before posting.",
    }
    return stubs.get(pillar, f"Here is the honest version of {product}.")


def _bundle_title(candidate: dict, pillar: str) -> str:
    product = str(candidate.get("product") or "").strip()
    claimed = str(candidate.get("claimed_change") or "").strip()
    if product and claimed:
        return f"{product}: {claimed}"[:80]
    if product:
        return product[:80]
    if claimed:
        return claimed[:80]
    raw = str(candidate.get("raw_text") or "").strip()
    return raw[:60] or pillar.replace("_", " ").title()


def _bundle_id(candidate_id: str, pillar: str) -> str:
    text = f"{pillar}:{candidate_id}".encode("utf-8")
    return hashlib.md5(text).hexdigest()[:8]


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_bundles(candidates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert verified candidates into content bundles.

    candidates_df must contain columns from the Candidate model.
    Only candidates eligible for bundle generation (as determined by
    verification/checker.can_become_bundle) should be passed in.
    """
    from saveloop.verification.checker import can_become_bundle

    bundles: list[dict] = []

    for _, row in candidates_df.iterrows():
        candidate = row.to_dict()

        # Guard — should already be filtered upstream, but enforce here too
        if not can_become_bundle(candidate):
            continue

        theme  = str(candidate.get("theme", "")).strip()
        pillar = _detect_pillar(theme)
        cfg    = _PILLAR[pillar]
        cid    = str(candidate.get("candidate_id", ""))
        confidence = float(candidate.get("confidence") or 0.0)
        keyword = (
            str(candidate.get("product") or "")
            or str(candidate.get("claimed_change") or "")
            or str(candidate.get("raw_text") or "")
        )[:60]

        bundles.append({
            "bundle_id":          _bundle_id(cid, pillar),
            "bundle_title":       _bundle_title(candidate, pillar),
            "trend_keyword":      keyword,
            "theme":              theme,
            "pillar":             pillar,
            "angle":              _angle(candidate, pillar),
            "format":             cfg["format"],
            "hook_style":         cfg["hook_style"],
            "hook":               _hook(candidate, pillar),
            "caption_direction":  _caption_direction(pillar),
            "caption_stub":       _caption_stub(candidate, pillar),
            "visual_direction":   cfg["visual_direction"],
            "aesthetic_tags":     cfg["aesthetic_tags"],
            "posting_window":     cfg["posting_window"],
            "cta":                cfg["cta"],
            "hashtags":           cfg["hashtags"],
            "priority_score":     round(confidence, 3),
            "status":             "draft",
            "notes":              str(candidate.get("verification_notes", "")),
            "candidate_id":       cid,
            "verification_label": str(candidate.get("verification_label", "")),
        })

    bundles_df = pd.DataFrame(bundles)
    if bundles_df.empty:
        return bundles_df
    return bundles_df.sort_values(
        ["priority_score", "trend_keyword"], ascending=[False, True]
    ).reset_index(drop=True)
