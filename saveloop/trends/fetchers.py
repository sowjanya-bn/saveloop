from __future__ import annotations

import hashlib
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

# ── Seed terms for each watchdog theme ───────────────────────────────────────

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

# Reddit communities relevant to the watchdog niche
SUBREDDITS = [
    ("Shrinkflation",       "shrinkflation"),
    ("Frugal",              "shrinkflation"),
    ("UKPersonalFinance",   "fake_deals"),
    ("mildlyinfuriating",   "shrinkflation"),
    ("assholedesign",       "fake_deals"),
    ("CasualUK",            "single_person"),
    ("UniUK",               "single_person"),
]

# Keywords that signal watchdog relevance — used to filter Reddit noise
NICHE_SIGNALS = {
    "shrinkflation": ["smaller", "size", "shrink", "weight", "gram", "ml", "reduced",
                      "less", "price", "£", "unit"],
    "fake_deals":    ["deal", "offer", "save", "discount", "loyalty", "clubcard", "nectar",
                      "unit price", "per 100g"],
    "single_person": ["one person", "cooking for one", "solo", "single", "bulk", "waste",
                      "just me"],
    "subscriptions": ["subscription", "cancel", "monthly", "worth it", "delivery pass",
                      "prime", "plus"],
}

# RSS sources — (url, theme)
RSS_FEEDS = [
    ("https://www.moneysavingexpert.com/rss/news/",   "fake_deals"),
    ("https://www.which.co.uk/news/rss",              "shrinkflation"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml","shrinkflation"),
]


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
                time.sleep(1.2)
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


# ── RSS fetcher ───────────────────────────────────────────────────────────────

def _fetch_rss(feeds: list[tuple[str, str]]) -> list[dict]:
    import requests
    import xml.etree.ElementTree as ET

    rows: list[dict] = []
    today = date.today().isoformat()
    headers = {"User-Agent": "saveloop-rss-fetcher/1.0"}

    for url, theme in feeds:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            for item in items[:10]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not title or not _is_relevant(_clean_title(title), theme):
                    continue
                rows.append({
                    "source": f"rss/{url.split('/')[2]}",
                    "theme": theme,
                    "keyword": _clean_title(title),
                    "momentum_score": 0.60,   # RSS signals get a baseline score
                    "observed_at": today,
                    "notes": link[:120],
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


# ── Convert trend rows to candidate dicts ─────────────────────────────────────

def _rows_to_candidates(rows: list[dict]) -> list[dict]:
    today = date.today().isoformat()
    candidates = []
    for row in rows:
        raw_text = str(row["keyword"])
        cid = "tr_" + hashlib.md5(f"{row['source']}:{raw_text}".encode()).hexdigest()[:10]
        candidates.append({
            "candidate_id": cid,
            "source": row["source"],
            "raw_text": raw_text,
            "theme": row["theme"],
            "product": None,
            "retailer": None,
            "claimed_change": None,
            "old_value": None,
            "new_value": None,
            "unit_price_before": None,
            "unit_price_after": None,
            "verified_increase_pct": None,
            "source_url": row.get("notes", ""),
            "submitted_by": None,
            "observed_at": today,
            "status": "new",
            "verification_label": "unverified",
            "verification_notes": "",
            "confidence": float(row.get("momentum_score", 0.0)),
        })
    return candidates


def _append_to_candidates(candidates: list[dict]) -> int:
    """Append new candidate rows to candidates.csv. Returns count added."""
    from saveloop.io.loaders import load_candidates

    paths = project_paths()
    cand_path = paths["raw_data_dir"] / "candidates.csv"

    try:
        existing = load_candidates(cand_path)
        existing_ids = set(existing["candidate_id"].tolist())
    except Exception:
        existing = pd.DataFrame()
        existing_ids = set()

    new_rows = [c for c in candidates if c["candidate_id"] not in existing_ids]
    if not new_rows:
        return 0

    new_df = pd.DataFrame(new_rows)
    combined = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(cand_path, index=False)
    return len(new_rows)


# ── Public API ────────────────────────────────────────────────────────────────

def fetch_fresh_trends(
    use_google: bool = True,
    use_reddit: bool = True,
    use_rss: bool = True,
    save: bool = True,
) -> pd.DataFrame:
    """
    Pull signals from Google Trends, Reddit, and RSS feeds.

    - Saves a trends_snapshot.csv for display in the Advanced tab.
    - Also appends new signals as Candidates (status: new) to candidates.csv.
    - Returns a trends-format DataFrame (backward compatible with score_trends).
    """
    rows: list[dict] = []

    if use_google:
        rows += _fetch_google_trends(SEEDS)

    if use_reddit:
        rows += _fetch_reddit(SUBREDDITS)

    if use_rss:
        rows += _fetch_rss(RSS_FEEDS)

    if not rows:
        return load_trends()

    fresh_df = pd.DataFrame(_deduplicate(rows))

    # Keep manual entries not duplicated by fresh data
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

    # Populate candidates.csv with new signals
    candidates = _rows_to_candidates(_deduplicate(rows))
    _append_to_candidates(candidates)

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
