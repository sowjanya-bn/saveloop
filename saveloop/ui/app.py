from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from saveloop.generation.color_schemes import PALETTES, palette_for_week
from saveloop.generation.post_assembler import build_post_plan, export_instagram_pack, save_post_plan
from saveloop.generation.post_history import all_history, mark_posted, posted_keywords
from saveloop.generation.weekly_planner import build_weekly_pack

ROOT = Path(__file__).resolve().parents[2]
trends_path     = ROOT / "data" / "raw"       / "trends_snapshot.csv"
bundles_path    = ROOT / "data" / "processed" / "content_bundles.csv"
summary_path    = ROOT / "data" / "reports"   / "weekly_summary.md"
posts_path      = ROOT / "data" / "processed" / "posts_log_with_metrics.csv"
post_plans_path = ROOT / "data" / "processed" / "post_plans.json"
catalog_path    = ROOT / "data" / "processed" / "weekly_catalog.json"

st.set_page_config(page_title="SaveLoop", layout="wide", page_icon="🔁")

_gemini_available = bool(os.getenv("GEMINI_API_KEY"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()

def _load_json_list(path: Path) -> list[dict]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    return []

def _save_json_list(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _current_week() -> str:
    iso = date.today().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def _log_to_catalog(plan: dict) -> None:
    catalog = _load_json_list(catalog_path)
    entry = {
        "bundle_id":    plan.get("bundle_id"),
        "bundle_title": plan.get("bundle_title"),
        "trend_keyword":plan.get("trend_keyword"),
        "theme":        plan.get("theme"),
        "format":       plan.get("format"),
        "hook":         plan.get("hook"),
        "posted_at":    date.today().isoformat(),
        "week":         _current_week(),
        "logged_at":    datetime.now(timezone.utc).isoformat(),
    }
    catalog = [c for c in catalog if not (
        c.get("bundle_id") == entry["bundle_id"] and c.get("week") == entry["week"]
    )]
    catalog.append(entry)
    _save_json_list(catalog_path, catalog)

def _this_week_catalog() -> list[dict]:
    return [c for c in _load_json_list(catalog_path) if c.get("week") == _current_week()]

def _this_week_keywords() -> set[str]:
    return {str(c.get("trend_keyword", "")).lower() for c in _this_week_catalog()}


# ── Load data ─────────────────────────────────────────────────────────────────

trends_df   = _load_csv(trends_path)
bundles_df  = _load_csv(bundles_path)
posts_df    = _load_csv(posts_path)
catalog     = _this_week_catalog()
this_week   = _current_week()


# ── Header ────────────────────────────────────────────────────────────────────

week_num   = date.today().isocalendar()[1]
palette    = palette_for_week(week_num)
used_topics = posted_keywords(lookback_weeks=8)

st.title("SaveLoop")
st.caption(f"{this_week}  ·  budget recipes · grocery swaps · Sunday resets  ·  this week's colour: **{palette['name']}**")
st.divider()


# ── Tabs ──────────────────────────────────────────────────────────────────────

weekly_tab, advanced_tab, performance_tab = st.tabs([
    "This Week's Content", "Advanced", "Performance"
])


# ═══════════════════════════════════════════════════════════════════════════════
# THIS WEEK'S CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

with weekly_tab:
    # ── What's been posted this week
    if catalog:
        posted_keywords = [c.get("trend_keyword", "") for c in catalog]
        st.success(f"Already posted this week: {' · '.join(f'`{k}`' for k in posted_keywords)}")
        st.caption("New packs will avoid these topics automatically.")
        st.divider()

    # ── Schedule preview
    st.markdown("""
**This week's plan:**

| Day | Pillar | Best posting time |
|---|---|---|
| Tuesday | Weeknight recipe | 17:00–19:00 |
| Wednesday | Grocery swap | 10:00–12:00 |
| Sunday | Sunday reset | 08:00–10:00 |
""")

    if not _gemini_available:
        st.warning("Set `GEMINI_API_KEY` in `.env` for real slide content. Without it, slides will be placeholder text.")

    st.divider()

    # ── Main action
    # Colour wheel preview
    st.markdown("**Colour rotation — 8-week spectrum:**")
    swatch_cols = st.columns(8)
    for i, (col, pal) in enumerate(zip(swatch_cols, PALETTES)):
        is_current = (i == week_num % 8)
        bg = "#{:02x}{:02x}{:02x}".format(*pal["bg"])
        ac = "#{:02x}{:02x}{:02x}".format(*pal["accent"])
        border = "3px solid #000" if is_current else "1px solid #ccc"
        col.markdown(
            f'<div style="background:{bg};border:{border};border-radius:8px;padding:8px 4px;text-align:center">'
            f'<div style="background:{ac};height:8px;border-radius:4px;margin-bottom:4px"></div>'
            f'<span style="font-size:11px;color:#555">{"→ " if is_current else ""}{pal["name"]}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.divider()

    if st.button("🗓 Generate this week's 3 posts", type="primary", use_container_width=True):
        with st.spinner("Picking topics · writing copy · rendering slides… (~30 seconds with Gemini)"):
            try:
                provider = "gemini" if _gemini_available else "rule_based"
                zip_bytes, meta = build_weekly_pack(text_provider=provider)
                st.session_state["_weekly_zip"]          = zip_bytes
                st.session_state["_weekly_zip_name"]     = f"saveloop_{this_week}.zip"
                st.session_state["_weekly_generated_at"] = datetime.now().strftime("%H:%M")
                st.session_state["_weekly_meta"]         = meta
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
                st.exception(exc)

    if st.session_state.get("_weekly_zip"):
        meta = st.session_state.get("_weekly_meta", {})
        st.success(f"Ready — {meta.get('palette','?')} palette · generated at {st.session_state.get('_weekly_generated_at', '')}")

        st.download_button(
            label="⬇  Download this week's content pack (.zip)",
            data=st.session_state["_weekly_zip"],
            file_name=st.session_state.get("_weekly_zip_name", "saveloop_weekly.zip"),
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )

        st.caption("""
**Inside the zip:**
```
posting_schedule.txt       ← exact days, times, hooks at a glance
1_Tuesday_<topic>/
   slide_01_cover.png      ← upload these 7 slides as a carousel
   slide_02_content.png
   ...
   slide_07_cta.png
   caption.txt             ← paste this directly into Instagram
   hashtags.txt
2_Wednesday_<topic>/
3_Sunday_<topic>/
```
""")

        with st.expander("After posting — log it here"):
            st.caption("Keeps track so next week's pack picks fresh topics.")
            bundles_df_fresh = _load_csv(bundles_path)
            if not bundles_df_fresh.empty:
                options = bundles_df_fresh["bundle_title"].tolist()
                to_log = st.multiselect("Which posts did you publish?", options)
                if st.button("Mark as posted") and to_log:
                    posted_df = bundles_df_fresh[bundles_df_fresh["bundle_title"].isin(to_log)]
                    for _, row in posted_df.iterrows():
                        _log_to_catalog(row.to_dict())
                        bundles_df_fresh.loc[bundles_df_fresh["bundle_id"] == row["bundle_id"], "status"] = "posted"
                    bundles_df_fresh.to_csv(bundles_path, index=False)
                    st.success("Logged. Next week's pack will pick new topics.")
                    st.rerun()

    # ── Refresh trends inline
    st.divider()
    with st.expander("Refresh trend signals first (optional)"):
        st.caption("Pulls this week's top posts from Reddit and rising queries from Google Trends UK.")
        if st.button("🔄 Fetch fresh trends"):
            with st.spinner("Fetching… (~20 seconds)"):
                try:
                    from saveloop.trends.fetchers import fetch_fresh_trends
                    from saveloop.trends.scoring import score_trends as _score
                    fresh = _score(fetch_fresh_trends())
                    st.success(f"Fetched {len(fresh)} signals. Generate the pack to use them.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Fetch failed: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED — single post, bundle board, trends
# ═══════════════════════════════════════════════════════════════════════════════

with advanced_tab:
    adv_trends, adv_bundles, adv_single = st.tabs(["Trends", "Bundle Board", "Single Post"])

    with adv_trends:
        st.subheader("Trend snapshot")
        if trends_df.empty:
            st.info("No trends yet. Use 'Fetch fresh trends' on the main tab.")
        else:
            st.dataframe(trends_df, use_container_width=True, hide_index=True)

    with adv_bundles:
        st.subheader("Bundle board")
        if bundles_df.empty:
            st.info("No bundles yet.")
        else:
            status_options = ["draft", "shortlisted", "selected", "posted", "archived"]
            editable = bundles_df[[c for c in [
                "bundle_id", "bundle_title", "pillar", "trend_keyword",
                "format", "posting_window", "priority_score", "status", "notes",
            ] if c in bundles_df.columns]].copy()
            edited = st.data_editor(
                editable, use_container_width=True, hide_index=True,
                column_config={"status": st.column_config.SelectboxColumn(options=status_options)},
                key="bundle_editor",
            )
            if st.button("Save changes"):
                merged = bundles_df.drop(columns=[c for c in ["status", "notes"] if c in bundles_df.columns]).merge(
                    edited[["bundle_id", "status", "notes"]], on="bundle_id", how="left"
                )
                merged.to_csv(bundles_path, index=False)
                st.success("Saved.")
                st.rerun()

    with adv_single:
        st.subheader("Single post studio")
        if bundles_df.empty:
            st.info("No bundles available.")
        else:
            this_week_kws = _this_week_keywords()

            def _label(row: pd.Series) -> str:
                kw = str(row.get("trend_keyword", "")).lower()
                flag = " ⚠ done this week" if kw in this_week_kws else ""
                return f"{row['bundle_title']} ({row.get('pillar','')}, {row['priority_score']:.2f}){flag}"

            opts = bundles_df.sort_values("priority_score", ascending=False)
            selected_id = st.selectbox(
                "Bundle",
                options=opts["bundle_id"].tolist(),
                format_func=lambda x: _label(opts[opts["bundle_id"] == x].iloc[0]),
            )
            selected_bundle = opts[opts["bundle_id"] == selected_id].iloc[0].to_dict()

            if st.button("Generate", type="primary"):
                provider = "gemini" if _gemini_available else "rule_based"
                with st.spinner("Generating…"):
                    plan = build_post_plan(selected_bundle, text_provider=provider)
                    st.session_state["_single_plan"] = plan

            plan = st.session_state.get("_single_plan")
            if plan and plan.get("bundle_id") == selected_id:
                st.markdown(f"**Hook:** {plan['hook']}")
                st.markdown(f"**Caption:**\n\n{plan['caption']}")
                if plan.get("slides"):
                    with st.expander("Slides"):
                        for i, s in enumerate(plan["slides"], 2):
                            st.markdown(f"**{i}. {s['title']}** — {s['body']}")

                if st.button("Prepare pack"):
                    with st.spinner("Rendering slides…"):
                        try:
                            zb = export_instagram_pack(plan)
                            st.session_state["_single_zip"] = zb
                            st.session_state["_single_zip_name"] = f"saveloop_{plan.get('bundle_id')}.zip"
                        except Exception as exc:
                            st.error(str(exc))

                if st.session_state.get("_single_zip"):
                    st.download_button(
                        "⬇ Download pack",
                        data=st.session_state["_single_zip"],
                        file_name=st.session_state.get("_single_zip_name", "pack.zip"),
                        mime="application/zip",
                    )


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

with performance_tab:
    st.subheader("Performance")

    # ── Full post history
    history = all_history()
    if history:
        st.markdown("#### Post history (all weeks)")
        rows = []
        for entry in reversed(history):
            for post in entry.get("posts", []):
                rows.append({
                    "week":          entry.get("week"),
                    "palette":       entry.get("palette"),
                    "day":           post.get("post_day"),
                    "topic":         post.get("bundle_title"),
                    "keyword":       post.get("trend_keyword"),
                    "pillar":        post.get("pillar"),
                    "hook":          post.get("hook"),
                    "published":     "✓" if post.get("published") else "—",
                })
        hist_df = pd.DataFrame(rows)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        # Mark as published
        with st.expander("Mark posts as published"):
            all_topics = [r["topic"] for r in rows if r["published"] == "—"]
            to_mark = st.multiselect("Select posts you actually published", all_topics)
            if st.button("Mark published") and to_mark:
                for title in to_mark:
                    mark_posted(title)
                st.success("Updated.")
                st.rerun()

        # Topics used — handy at a glance
        all_keywords = [r["keyword"] for r in rows]
        st.markdown(f"**Topics covered so far ({len(all_keywords)}):** " +
                    "  ".join(f"`{k}`" for k in sorted(set(all_keywords))))
        st.divider()

    if summary_path.exists():
        st.markdown(summary_path.read_text(encoding="utf-8"))
    else:
        st.info("Run `python -m saveloop.cli report` to generate a performance summary.")

    if not posts_df.empty:
        cols = [c for c in ["post_id","bundle_id","pattern","aesthetic_tags","J_score","engagement_rate","win_flag"] if c in posts_df.columns]
        st.dataframe(posts_df[cols], use_container_width=True, hide_index=True)
