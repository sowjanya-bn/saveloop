# SaveLoop Enhancement Spec
### v1.0 — Consumer Watchdog Pivot
*Created: May 2026. Redirecting the existing SaveLoop pipeline from lifestyle/food content to community-powered money forensics.*

---

## Overview

SaveLoop already has a working pipeline: trend ingestion → bundle generation → Streamlit board → post history → metrics → weekly summary. The infrastructure is good. The content identity was not sharp enough.

This spec defines the minimum changes needed to redirect SaveLoop toward verified consumer intelligence. The generation layer, brief format, metrics system and Streamlit UI are preserved. What changes is upstream of bundle generation.

**The pivot in one sentence:** Replace trend signals with verified candidate claims. Everything downstream stays the same.

---

## What Does Not Change

- Bundle schema (with two field additions — see below)
- Bundle generator architecture
- Script generator and carousel renderer
- Brief format (hook, shot list, overlays, CTA)
- Streamlit UI board (with one new tab — see below)
- Metrics system (saves remains the primary signal)
- Weekly summary and reporting
- Post history and log structure
- CLI commands (`bundles`, `analyze`, `report`, `run`)

---

## What Changes

### 1. Content Pillars — Replace in `bundles/generator.py`

**Remove:**
- `weeknight_recipes`
- `grocery_swaps`
- `sunday_reset`
- `general`

**Replace with:**

| Pillar | Theme | Hook Style | Format |
|---|---|---|---|
| `shrinkflation_watch` | Product size/weight reduction at same or higher price | Outrage + reveal | Carousel or Reel |
| `fake_deal_forensics` | Multi-buy, loyalty and was/now pricing that does not hold up | Forensic reveal | Carousel |
| `single_person_tax` | Hidden cost premium for one-person households | Empathy + maths | Reel or Carousel |
| `subscription_trap` | Subscriptions and passes that cost more than they save | Break-even reveal | Reel |
| `honest_meal_cost` | Budget meal content including all pro-rata costs | Honest utility | Reel |
| `reddit_verified` | Community-sourced stories verified by SaveLoop | Story + lesson | Reel or Carousel |
| `saveloop_flag` | Reader-submitted money leaks, verified before posting | Community reveal | Carousel or Single |

**Pillar config structure** (same fields as existing `_PILLAR` dict, new values):

```python
_PILLAR = {
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
```

---

### 2. Trend Signal Source — Replace in `trends/fetchers.py`

**Remove:**
- `SEEDS` (food/lifestyle keywords)
- `SUBREDDITS` (EatCheapAndHealthy, MealPrepSunday, simpleliving)
- `NICHE_SIGNALS` (food/lifestyle keyword filters)

**Replace with:**

```python
SEEDS = {
    "shrinkflation": [
        "shrinkflation UK",
        "supermarket price increase",
        "smaller packaging same price",
        "product size reduced",
        "unit price increase",
    ],
    "fake_deals": [
        "supermarket fake deal",
        "loyalty card price",
        "was now pricing",
        "multi-buy not worth it",
        "unit price comparison",
    ],
    "single_person": [
        "cooking for one budget",
        "single person food waste",
        "bulk buy not worth it solo",
        "one person grocery cost",
    ],
    "subscriptions": [
        "subscription not worth it",
        "cancel delivery pass",
        "streaming too expensive",
        "subscription trap UK",
    ],
}

SUBREDDITS = [
    ("Shrinkflation",       "shrinkflation"),
    ("Frugal",              "shrinkflation"),
    ("UKPersonalFinance",   "fake_deals"),
    ("mildlyinfuriating",   "shrinkflation"),
    ("assholedesign",       "fake_deals"),
    ("CasualUK",            "single_person"),
    ("UniUK",               "single_person"),
]

NICHE_SIGNALS = {
    "shrinkflation": ["smaller", "size", "shrink", "weight", "gram", "ml", "reduced", "less", "price", "£", "unit"],
    "fake_deals":    ["deal", "offer", "save", "discount", "loyalty", "clubcard", "nectar", "unit price", "per 100g"],
    "single_person": ["one person", "cooking for one", "solo", "single", "bulk", "waste", "just me"],
    "subscriptions": ["subscription", "cancel", "monthly", "worth it", "delivery pass", "prime", "plus"],
}
```

**Also add RSS sources** (new method `_fetch_rss` alongside existing fetchers):

```python
RSS_FEEDS = [
    ("https://www.moneysavingexpert.com/rss/news/", "fake_deals"),
    ("https://www.which.co.uk/news/rss", "shrinkflation"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml", "shrinkflation"),
]
```

---

### 3. Candidate Model — New file `models/candidate.py`

This is the new upstream stage. Candidates are raw claims before they become bundles.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

@dataclass
class Candidate:
    candidate_id: str
    source: str                    # reddit/r/X | rss/which | submission | manual
    raw_text: str                  # original text or submission content
    theme: str                     # shrinkflation | fake_deals | single_person | subscriptions
    product: Optional[str] = None  # product name if identifiable
    retailer: Optional[str] = None
    claimed_change: Optional[str] = None  # "box reduced from 400g to 350g"
    old_value: Optional[str] = None       # price or size before
    new_value: Optional[str] = None       # price or size after
    unit_price_before: Optional[float] = None
    unit_price_after: Optional[float] = None
    verified_increase_pct: Optional[float] = None
    source_url: Optional[str] = None
    submitted_by: Optional[str] = None    # anonymous token for community submissions
    observed_at: str = field(default_factory=lambda: date.today().isoformat())
    
    # Verification workflow
    status: str = "new"  
    # new | pending_review | verified | needs_more_evidence | rejected | duplicate | posted
    
    verification_label: str = "unverified"
    # verified | reader_submitted_checking | interesting_unconfirmed
    
    verification_notes: str = ""
    confidence: float = 0.0  # 0.0–1.0, set during verification
```

---

### 4. Verification Layer — New file `verification/checker.py`

Sits between candidate ingestion and bundle generation. Candidates must pass through here before becoming bundles.

**Verification checklist (enforced in UI and CLI):**
- Claim is specific: product name, retailer, size/price identified
- Current unit price confirmed from live source or receipt
- Before price/size confirmed from archived source, receipt or multiple corroborating reports
- Maths checked: unit price increase calculated and noted
- No ambiguity about retailer or product variant

**Verification statuses and public labels:**

| Internal Status | Public Label | Meaning |
|---|---|---|
| `verified` | ✓ Verified by SaveLoop | Numbers checked, claim confirmed |
| `pending_review` | 👀 Reader-submitted, checking | Under verification, not yet confirmed |
| `needs_more_evidence` | ~ Interesting, unconfirmed | Flagged but evidence incomplete |
| `rejected` | (not posted) | Claim not accurate or not a money leak |
| `duplicate` | (not posted) | Already in the system |

**Hard rule: nothing enters the bundle generator with `verification_required: True` unless status is `verified`.**

---

### 5. Bundle Model — Add two fields to `models/bundle.py`

```python
@dataclass
class ContentBundle:
    # ... existing fields unchanged ...
    
    # New fields
    candidate_id: str = ""           # links back to source candidate
    verification_label: str = ""     # carried through to post and shown publicly
```

---

### 6. Streamlit UI — Add one tab to `ui/app.py`

Add a **Verification Board** tab alongside the existing Bundle Board.

**Verification Board shows:**
- All candidates with status `new` and `pending_review`
- For each candidate: raw text, source, identified product/retailer, claimed change
- Action buttons: Mark Verified / Needs Evidence / Reject / Duplicate
- Notes field for verification evidence
- "Send to Bundle Generator" button (only active when status is `verified`)

**Existing Bundle Board:** unchanged except add `verification_label` column display.

---

### 7. Community Submission Intake — New file `integrations/submissions.py`

Minimal first version: reads a Google Sheets CSV export (from a public Google Form) into the candidates table. No live API required for MVP.

**Form fields map to Candidate fields:**
- Product name → `product`
- Retailer → `retailer`  
- What changed → `claimed_change`
- Old size/price → `old_value`
- New size/price → `new_value`
- Location/date → `verification_notes`
- Contact (optional) → `submitted_by` (stored as anonymous token)

**Intake sets status to `pending_review` and `verification_label` to `reader_submitted_checking` automatically.**

---

## Migration Plan

### Step 1 — Config only (30 minutes)
Replace `SEEDS`, `SUBREDDITS` and `NICHE_SIGNALS` in `trends/fetchers.py` with new watchdog values. Run `python -m saveloop.cli trends` and verify new signals are coming in.

### Step 2 — Pillars (1 hour)
Replace `_PILLAR` dict and detection signals in `bundles/generator.py`. Run `python -m saveloop.cli bundles` and verify bundles are generating with new themes.

### Step 3 — Candidate model (2 hours)
Add `models/candidate.py`. Add `data/raw/candidates.csv` as the new upstream data store. Write `io/loaders.py` extension to load candidates.

### Step 4 — Verification layer (2 hours)
Add `verification/checker.py`. Add verification status logic. Wire into CLI as `python -m saveloop.cli verify`.

### Step 5 — UI verification tab (2 hours)
Add Verification Board tab to `ui/app.py`. Status buttons, notes field, send-to-bundles action.

### Step 6 — Bundle linkage (1 hour)
Add `candidate_id` and `verification_label` to `ContentBundle`. Update bundle generator to pull from verified candidates rather than trends directly.

### Step 7 — Submissions intake (1 hour)
Add `integrations/submissions.py`. Test with a sample Google Form CSV export.

**Total estimated: one focused weekend.**

---

## What the Pipeline Looks Like After Enhancement

```
Signal Collection
  Reddit (new subreddits) + RSS (MSE, Which?, BBC) + Community submissions
  ↓
Candidate Pool (candidates.csv)
  status: new
  ↓
Triage & Clustering
  Deduplicate, theme-tag, flag high-signal candidates
  status: pending_review
  ↓
Verification Board (Streamlit tab)
  Human checks numbers, confirms claim
  status: verified | needs_more_evidence | rejected
  ↓
Bundle Generator (unchanged architecture, new pillars)
  Verified candidates → content bundles
  verification_label carried through
  ↓
Script Generator + Carousel Renderer (unchanged)
  ↓
Post with verification label shown publicly
  ↓
Metrics + Weekly Summary (unchanged)
```

---

## What the Brief Format Looks Like After Enhancement

**Before (sun_carousel.txt):**
```
Title: 5 Grocery Swaps to Save £10/week (Carousel)
Slides: hook; five swaps; CTA
Design: big type; high contrast; one accent colour; clean background
CTA: Save this. DM "LIST" for a printable
```

**After (example shrinkflation_watch brief):**
```
Title: McVitie's Digestives Lost 50g. The Price Didn't. (Carousel)
Verification: ✓ Verified by SaveLoop
Slides: hook (size change); old vs new (visual); unit price before; unit price after; % increase; practical alternative; CTA
Numbers: 400g → 350g | £1.49 → £1.49 | 37p/100g → 43p/100g | +16% real increase
Design: high contrast; before/after split; bold number overlay; verified badge
CTA: Save this before your next shop
```

---

## Files Changed Summary

| File | Change Type |
|---|---|
| `trends/fetchers.py` | Replace SEEDS, SUBREDDITS, NICHE_SIGNALS |
| `bundles/generator.py` | Replace _PILLAR dict and detection signals |
| `models/bundle.py` | Add candidate_id and verification_label fields |
| `models/candidate.py` | **New file** |
| `verification/checker.py` | **New file** |
| `integrations/submissions.py` | **New file** |
| `ui/app.py` | Add Verification Board tab |
| `io/loaders.py` | Add candidate loader |
| `data/raw/candidates.csv` | **New data store** |

Everything else: unchanged.

---

*Save as: `docs/SAVELOOP_ENHANCEMENT_SPEC_v1.0.md`*
*Vetted by: GPT (pending)*
*Previous spec: `SAVELOOP_PIPELINE_SPEC_v0.1.md`*
*Next: `SAVELOOP_FOOD_NETWORK_SPEC_v0.1.md` (bulk split and meal sharing layer)*
