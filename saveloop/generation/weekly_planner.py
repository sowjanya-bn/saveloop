from __future__ import annotations

import io
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from saveloop.bundles.generator import generate_bundles
from saveloop.generation.carousel_renderer import render_carousel
from saveloop.generation.color_schemes import palette_for_week
from saveloop.generation.post_assembler import build_post_plan
from saveloop.generation.post_history import log_weekly_pack, posted_keywords
from saveloop.trends.fetchers import load_trends
from saveloop.trends.scoring import score_trends

PILLAR_SCHEDULE = [
    ("weeknight_recipes", "Tuesday",   "17:00–19:00"),
    ("grocery_swaps",     "Wednesday", "10:00–12:00"),
    ("sunday_reset",      "Sunday",    "08:00–10:00"),
]


def _best_bundle_per_pillar(bundles_df: pd.DataFrame, exclude_keywords: set[str]) -> list[dict]:
    selected = []
    used_this_run: set[str] = set()

    for pillar, day, window in PILLAR_SCHEDULE:
        pool = bundles_df[bundles_df["pillar"] == pillar].sort_values("priority_score", ascending=False)

        # Prefer topics not seen in recent weeks
        fresh_pool = pool[~pool["trend_keyword"].str.lower().isin(exclude_keywords | used_this_run)]
        chosen = fresh_pool if not fresh_pool.empty else pool

        if chosen.empty:
            continue

        row = chosen.iloc[0].to_dict()
        row["_post_day"] = day
        row["_post_window"] = window
        used_this_run.add(row["trend_keyword"].lower())
        selected.append(row)

    return selected


def _make_folder_name(index: int, bundle: dict) -> str:
    day = bundle.get("_post_day", f"post{index + 1}")
    kw = bundle.get("trend_keyword", "post")
    safe = "".join(c if c.isalnum() or c in "- " else "" for c in kw).strip().replace(" ", "_")[:30]
    return f"{index + 1}_{day}_{safe}"


def _schedule_txt(bundles: list[dict], plans: list[dict], palette_name: str) -> str:
    week = date.today().isocalendar()
    lines = [
        f"WEEK {week[0]}-W{week[1]:02d} — POST SCHEDULE",
        f"Colour theme: {palette_name}",
        "=" * 42, "",
    ]
    for i, (bundle, plan) in enumerate(zip(bundles, plans), start=1):
        folder = _make_folder_name(i - 1, bundle)
        lines += [
            f"Post {i}: {bundle['_post_day']}  {bundle['_post_window']}",
            f"Topic:  {bundle['bundle_title']}",
            f"Hook:   {plan['hook']}",
            f"Folder: {folder}/",
            "",
        ]
    lines += [
        "Tips for going viral:",
        "- Post at the start of your window, not the end",
        "- Reply to every comment in the first 30 minutes",
        "- Add caption before uploading — don't edit after posting",
        "- Use the save CTA in your first Story straight after",
    ]
    return "\n".join(lines)


def build_weekly_pack(
    text_provider: str = "gemini",
    output_dir: Path | None = None,
) -> tuple[bytes, dict]:
    """
    Generate one full week of content.
    Returns (zip_bytes, metadata) where metadata has palette name, topics, etc.
    """
    import tempfile
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())

    # This week's colour palette
    week_num = date.today().isocalendar()[1]
    palette = palette_for_week(week_num)

    # Load trends → bundles, excluding recently used topics
    trends_df = score_trends(load_trends())
    bundles_df = generate_bundles(trends_df)
    exclude = posted_keywords(lookback_weeks=8)
    selected_bundles = _best_bundle_per_pillar(bundles_df, exclude)

    if not selected_bundles:
        raise ValueError("No bundles available — run trends first.")

    # Generate plans and render slides
    plans: list[dict] = []
    slide_path_groups: list[list[Path]] = []

    for i, bundle in enumerate(selected_bundles):
        plan = build_post_plan(bundle, text_provider=text_provider)
        plans.append(plan)

        slide_dir = output_dir / _make_folder_name(i, bundle)
        slide_paths = render_carousel(plan, output_dir=slide_dir, palette=palette)
        slide_path_groups.append(slide_paths)

    # Log to history before zipping
    log_weekly_pack(selected_bundles, plans, palette["name"])

    # Build master zip
    master_buf = io.BytesIO()
    week_label = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]:02d}"

    with zipfile.ZipFile(master_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("posting_schedule.txt", _schedule_txt(selected_bundles, plans, palette["name"]))

        for i, (bundle, plan, slide_paths) in enumerate(zip(selected_bundles, plans, slide_path_groups)):
            folder = _make_folder_name(i, bundle)

            for path in slide_paths:
                zf.write(path, arcname=f"{folder}/{path.name}")

            caption = plan.get("caption", "").strip()
            cta = plan.get("closing_cta", "").strip()
            if cta and not caption.rstrip(".").endswith(cta.rstrip(".")):
                caption = f"{caption}\n\n{cta}"
            zf.writestr(f"{folder}/caption.txt", caption)

            tags = "\n".join(t.strip() for t in str(plan.get("hashtags") or "").split(",") if t.strip())
            zf.writestr(f"{folder}/hashtags.txt", tags)

    metadata = {
        "week": week_label,
        "palette": palette["name"],
        "palette_index": week_num % 8,
        "topics": [b["bundle_title"] for b in selected_bundles],
        "hooks": [p["hook"] for p in plans],
    }

    return master_buf.getvalue(), metadata
