from __future__ import annotations

import re
import time
from datetime import date
from pathlib import Path

import pandas as pd

from saveloop.config import project_paths

REQUIRED_TREND_COLUMNS = [
    "source",
    "theme",
    "keyword",
    "momentum_score",
    "observed_at",
    "notes",
]

# ── Seed terms for each content pillar ───────────────────────────────────────

SEEDS = {
    "food": [
        "budget weeknight dinners",
        "cheap family meals",
        "simple grocery swaps",
        "meal prep on a budget",
        "supermarket own brand",
    ],
    "lifestyle": [
        "Sunday reset routine",
        "weekly reset",
        "tiny Sunday habits",
    ],
}

# Reddit communities relevant to the niche
SUBREDDITS = [
    ("EatCheapAndHealthy", "food"),
    ("MealPrepSunday",     "food"),
    ("Frugal",             "food"),
    ("UKPersonalFinance",  "food"),
    ("simpleliving",       "lifestyle"),
]

# Keywords that signal pillar relevance — used to filter Reddit noise
NICHE_SIGNALS = {
    "food":      ["budget", "cheap", "meal", "recipe", "grocery", "dinner", "swap",
                  "cook", "food", "eat", "ingredient", "prep", "freezer", "£", "$"],
    "lifestyle": ["reset", "sunday", "routine", "habit", "simple", "slow", "calm",
                  "week", "morning", "checklist"],
}


# ── Google Trends fetcher ─────────────────────────────────────────────────────

def _fetch_google_trends(seeds: dict[str, list[str]]) -> list[dict]:
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return []

    rows: list[dict] = []
    today = date.today().isoformat()
    pytrends = TrendReq(hl="en-GB", tz=0, timeout=(10, 25))

    for theme, keywords in seeds.items():
        for seed in keywords:
            try:
                pytrends.build_payload([seed], timeframe="now 7-d", geo="GB")
                related = pytrends.related_queries()
                data = related.get(seed, {})

                for query_type, score_scale in [("rising", 0.85), ("top", 0.70)]:
                    df = data.get(query_type)
                    if df is None or df.empty:
                        continue
                    for _, qrow in df.head(5).iterrows():
                        kw = str(qrow.get("query", "")).strip().lower()
                        if not kw or len(kw) < 5:
                            continue
                        val = float(qrow.get("value", 50)) / 100.0
                        momentum = round(min(score_scale, score_scale * 0.5 + val * 0.5), 3)
                        rows.append({
                            "source": "google_trends",
                            "theme": theme,
                            "keyword": kw,
                            "momentum_score": momentum,
                            "observed_at": today,
                            "notes": f"related to '{seed}' ({query_type})",
                        })
                time.sleep(1.2)   # be polite to the API
            except Exception:
                continue

    return rows


# ── Reddit fetcher ────────────────────────────────────────────────────────────

def _clean_title(title: str) -> str:
    title = re.sub(r"[^a-zA-Z0-9£$\s\-'']", " ", title)
    title = re.sub(r"\s+", " ", title).strip().lower()
    return title[:80]


def _is_relevant(title: str, theme: str) -> bool:
    signals = NICHE_SIGNALS.get(theme, [])
    return any(s in title for s in signals)


def _reddit_momentum(upvotes: int, num_comments: int) -> float:
    # Simple log-scaled score normalised to 0-1 range
    import math
    raw = math.log1p(upvotes) + math.log1p(num_comments) * 0.3
    return round(min(raw / 12.0, 0.95), 3)


def _fetch_reddit(subreddits: list[tuple[str, str]]) -> list[dict]:
    import requests

    rows: list[dict] = []
    today = date.today().isoformat()
    headers = {"User-Agent": "saveloop-trend-fetcher/1.0"}

    for subreddit, theme in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=25&t=week"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                d = post.get("data", {})
                title = _clean_title(d.get("title", ""))
                if not title or not _is_relevant(title, theme):
                    continue
                upvotes = int(d.get("ups", 0))
                comments = int(d.get("num_comments", 0))
                if upvotes < 50:
                    continue
                rows.append({
                    "source": f"reddit/r/{subreddit}",
                    "theme": theme,
                    "keyword": title,
                    "momentum_score": _reddit_momentum(upvotes, comments),
                    "observed_at": today,
                    "notes": f"{upvotes} upvotes, {comments} comments",
                })
            time.sleep(0.5)
        except Exception:
            continue

    return rows


# ── Deduplicate & merge ───────────────────────────────────────────────────────

def _deduplicate(rows: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for row in rows:
        kw = re.sub(r"\s+", " ", row["keyword"].lower().strip())
        kw = re.sub(r"[^a-z0-9£ ]", "", kw).strip()
        if not kw:
            continue
        if kw not in seen or row["momentum_score"] > seen[kw]["momentum_score"]:
            seen[kw] = {**row, "keyword": kw}
    return sorted(seen.values(), key=lambda r: r["momentum_score"], reverse=True)


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_fresh_trends(
    use_google: bool = True,
    use_reddit: bool = True,
    save: bool = True,
) -> pd.DataFrame:
    """
    Pull trend signals from Google Trends and/or Reddit.
    Merges with any existing manual entries, deduplicates, and optionally
    overwrites trends_snapshot.csv.
    """
    rows: list[dict] = []

    if use_google:
        rows += _fetch_google_trends(SEEDS)

    if use_reddit:
        rows += _fetch_reddit(SUBREDDITS)

    if not rows:
        return load_trends()

    fresh_df = pd.DataFrame(_deduplicate(rows))

    # Keep manual entries that are not duplicated by fresh data
    try:
        existing = load_trends()
        manual = existing[existing["source"].str.startswith("manual")]
        existing_kws = set(fresh_df["keyword"].str.lower())
        manual = manual[~manual["keyword"].str.lower().isin(existing_kws)]
        fresh_df = pd.concat([fresh_df, manual], ignore_index=True)
    except Exception:
        pass

    if save:
        paths = project_paths()
        out = paths["raw_data_dir"] / "trends_snapshot.csv"
        fresh_df.to_csv(out, index=False)

    return fresh_df


def load_trends(path: Path | None = None) -> pd.DataFrame:
    paths = project_paths()
    path = path or (paths["raw_data_dir"] / "trends_snapshot.csv")
    if not path.exists():
        raise SystemExit(f"Trend snapshot not found: {path}")

    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_TREND_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns in trends snapshot: {', '.join(missing)}")

    df["momentum_score"] = pd.to_numeric(df["momentum_score"], errors="coerce").fillna(0.0)
    for col in ["source", "theme", "keyword", "observed_at", "notes"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df
