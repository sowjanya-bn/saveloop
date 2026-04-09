from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORY_PATH = ROOT / "data" / "processed" / "post_history.json"


def _load() -> list[dict]:
    if HISTORY_PATH.exists():
        try:
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def _save(history: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def _current_week() -> str:
    iso = date.today().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def log_weekly_pack(bundles: list[dict], plans: list[dict], palette_name: str) -> None:
    """Record a generated weekly pack in the history."""
    history = _load()
    week = _current_week()

    # Remove any existing entry for this week (regeneration overwrites)
    history = [h for h in history if h.get("week") != week]

    posts = []
    for bundle, plan in zip(bundles, plans):
        posts.append({
            "bundle_id":     bundle.get("bundle_id"),
            "bundle_title":  bundle.get("bundle_title"),
            "trend_keyword": bundle.get("trend_keyword"),
            "pillar":        bundle.get("pillar"),
            "post_day":      bundle.get("_post_day"),
            "hook":          plan.get("hook"),
        })

    history.append({
        "week":        week,
        "generated":   date.today().isoformat(),
        "palette":     palette_name,
        "posts":       posts,
    })
    _save(history)


def posted_keywords(lookback_weeks: int = 8) -> set[str]:
    """
    Return all trend keywords posted in the last N weeks.
    Used to prevent topic repeats across weeks.
    """
    history = _load()
    today_iso = date.today().isocalendar()
    current_year, current_week = today_iso[0], today_iso[1]

    recent: set[str] = set()
    for entry in history:
        raw = str(entry.get("week", ""))
        try:
            year, w = int(raw[:4]), int(raw[6:])
        except (ValueError, IndexError):
            continue
        weeks_ago = (current_year - year) * 52 + (current_week - w)
        if 0 <= weeks_ago < lookback_weeks:
            for post in entry.get("posts", []):
                kw = str(post.get("trend_keyword", "")).lower().strip()
                if kw:
                    recent.add(kw)
    return recent


def all_history() -> list[dict]:
    return _load()


def mark_posted(bundle_title: str) -> None:
    """Mark a specific post as actually published (versus just generated)."""
    history = _load()
    week = _current_week()
    for entry in history:
        if entry.get("week") == week:
            for post in entry.get("posts", []):
                if post.get("bundle_title") == bundle_title:
                    post["published"] = True
                    post["published_date"] = date.today().isoformat()
    _save(history)
