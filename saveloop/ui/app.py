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
candidates_path = ROOT / "data" / "raw"       / "candidates.csv"
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
        "bundle_id":     plan.get("bundle_id"),
        "bundle_title":  plan.get("bundle_title"),
        "trend_keyword": plan.get("trend_keyword"),
        "theme":         plan.get("theme"),
        "format":        plan.get("format"),
        "hook":          plan.get("hook"),
        "posted_at":     date.today().isoformat(),
        "week":          _current_week(),
        "logged_at":     datetime.now(timezone.utc).isoformat(),
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

def _save_candidates(df: pd.DataFrame) -> None:
    candidates_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(candidates_path, index=False)


# ── Load data ─────────────────────────────────────────────────────────────────

trends_df   = _load_csv(trends_path)
bundles_df  = _load_csv(bundles_path)
posts_df    = _load_csv(posts_path)
catalog     = _this_week_catalog()
this_week   = _current_week()


# ── Header ────────────────────────────────────────────────────────────────────

week_num    = date.today().isocalendar()[1]
palette     = palette_for_week(week_num)
used_topics = posted_keywords(lookback_weeks=8)

st.title("SaveLoop")
st.caption(
    f"{this_week}  ·  consumer watchdog  ·  shrinkflation · fake deals · subscription traps"
    f"  ·  this week's colour: **{palette['name']}**"
)
st.divider()


# ── Tabs ──────────────────────────────────────────────────────────────────────

weekly_tab, verify_tab, advanced_tab, performance_tab = st.tabs([
    "This Week's Content", "Verification Board", "Advanced", "Performance"
])


# ═══════════════════════════════════════════════════════════════════════════════
# THIS WEEK'S CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

with weekly_tab:
    if catalog:
        posted_kws = [c.get("trend_keyword", "") for c in catalog]
        st.success(f"Already posted this week: {' · '.join(f'`{k}`' for k in posted_kws)}")
        st.caption("New packs will avoid these topics automatically.")
        st.divider()

    st.markdown("""
**This week's plan:**

| Day | Type | Pillars | Best posting time |
|---|---|---|---|
| Monday | Watchdog carousel | shrinkflation_watch · fake_deal_forensics | 10:00–12:00 |
| Wednesday | Story / Reel | reddit_verified · subscription_trap | 18:00–20:00 |
| Friday | Utility / Community | honest_meal_cost · saveloop_flag · single_person_tax | 17:00–19:00 |
""")

    if not _gemini_available:
        st.warning("Set `GEMINI_API_KEY` in `.env` for real slide content. Without it, slides will be placeholder text.")

    st.divider()

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
posting_schedule.txt       ← exact days, times, hooks, verification labels
1_Monday_<topic>/
   slide_01-07.png         ← upload as carousel or reel
   caption.txt
   hashtags.txt
2_Wednesday_<topic>/
3_Friday_<topic>/
```
""")

        with st.expander("After posting — log it here"):
            st.caption("Keeps track so next week's pack picks fresh topics.")
            bundles_df_fresh = _load_csv(bundles_path)
            if not bundles_df_fresh.empty:
                options = bundles_df_fresh["bundle_title"].tolist()
                to_log  = st.multiselect("Which posts did you publish?", options)
                if st.button("Mark as posted") and to_log:
                    posted_df = bundles_df_fresh[bundles_df_fresh["bundle_title"].isin(to_log)]
                    for _, row in posted_df.iterrows():
                        _log_to_catalog(row.to_dict())
                        bundles_df_fresh.loc[
                            bundles_df_fresh["bundle_id"] == row["bundle_id"], "status"
                        ] = "posted"
                    bundles_df_fresh.to_csv(bundles_path, index=False)
                    st.success("Logged. Next week's pack will pick new topics.")
                    st.rerun()

    st.divider()
    with st.expander("Refresh signal pool (optional)"):
        st.caption("Pulls this week's top posts from Reddit, rising queries from Google Trends UK, and RSS from MSE/Which/BBC.")
        if st.button("🔄 Fetch fresh signals"):
            with st.spinner("Fetching… (~20 seconds)"):
                try:
                    from saveloop.trends.fetchers import fetch_fresh_trends
                    from saveloop.trends.scoring import score_trends as _score
                    fresh = _score(fetch_fresh_trends())
                    st.success(f"Fetched {len(fresh)} signals. New candidates added to the Verification Board.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Fetch failed: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# VERIFICATION BOARD
# ═══════════════════════════════════════════════════════════════════════════════

with verify_tab:
    st.subheader("Verification Board")
    st.caption(
        "Review candidates before they enter bundle generation. "
        "Only **Verified** candidates (or honest_meal_cost) become posts."
    )

    from saveloop.verification.checker import (
        HUMAN_ONLY_STATUSES,
        validate_fields,
        calculate_unit_price_increase,
        set_status_human,
        can_become_bundle,
    )

    cands_df = _load_csv(candidates_path)

    # ── Stats bar
    if not cands_df.empty:
        total       = len(cands_df)
        n_verified  = int((cands_df["status"] == "verified").sum()) if "status" in cands_df.columns else 0
        n_pending   = int(cands_df["status"].isin(["new", "pending_review"]).sum()) if "status" in cands_df.columns else 0
        n_rejected  = int(cands_df["status"].isin(["rejected", "duplicate"]).sum()) if "status" in cands_df.columns else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total candidates",  total)
        c2.metric("Verified",          n_verified)
        c3.metric("Pending review",    n_pending)
        c4.metric("Rejected / Dup",    n_rejected)
        st.divider()

    # ── Filter to actionable candidates
    if cands_df.empty or "status" not in cands_df.columns:
        st.info("No candidates yet. Run 'Fetch fresh signals' or drop a submissions.csv into data/raw/.")
    else:
        pending_df = cands_df[cands_df["status"].isin(["new", "pending_review"])].copy()

        if pending_df.empty:
            st.success("No pending candidates. All caught up.")
        else:
            st.markdown(f"**{len(pending_df)} candidates awaiting review**")

            # Show summary table
            display_cols = [c for c in [
                "candidate_id", "status", "theme", "source", "product",
                "retailer", "claimed_change", "old_value", "new_value", "confidence",
            ] if c in pending_df.columns]
            st.dataframe(pending_df[display_cols], use_container_width=True, hide_index=True)

            st.divider()
            st.markdown("**Review a candidate**")

            cid_options = pending_df["candidate_id"].tolist()
            selected_cid = st.selectbox(
                "Select candidate ID",
                options=cid_options,
                format_func=lambda x: (
                    f"{x}  ·  "
                    + str(pending_df.loc[pending_df["candidate_id"] == x, "product"].values[0] or "")
                    + "  ·  "
                    + str(pending_df.loc[pending_df["candidate_id"] == x, "theme"].values[0] or "")
                ),
            )

            if selected_cid:
                row   = pending_df[pending_df["candidate_id"] == selected_cid].iloc[0].to_dict()
                missing_fields = validate_fields(row)
                pct_increase   = calculate_unit_price_increase(row)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Source:** `{row.get('source', '')}`")
                    st.markdown(f"**Theme:** `{row.get('theme', '')}`")
                    st.markdown(f"**Product:** {row.get('product') or '—'}")
                    st.markdown(f"**Retailer:** {row.get('retailer') or '—'}")
                    st.markdown(f"**Claimed change:** {row.get('claimed_change') or '—'}")
                with col_b:
                    st.markdown(f"**Old value:** {row.get('old_value') or '—'}")
                    st.markdown(f"**New value:** {row.get('new_value') or '—'}")
                    if pct_increase is not None:
                        st.markdown(f"**Calculated increase:** {pct_increase:.1f}%")
                    st.markdown(f"**Confidence:** {float(row.get('confidence') or 0):.2f}")
                    st.markdown(f"**Current status:** `{row.get('status', '')}`")

                st.markdown(f"**Raw text:** {row.get('raw_text', '')}")

                if missing_fields:
                    st.warning(f"Missing fields required for verification: {', '.join(missing_fields)}")

                existing_notes = str(row.get("verification_notes") or "")
                if existing_notes:
                    st.markdown(f"**Existing notes:** {existing_notes}")

                notes_input = st.text_area(
                    "Verification notes (evidence, source URL, calculation)",
                    placeholder="e.g. Checked Tesco.com 2026-05-17: 500g now £2.20 vs £1.80 in Feb (receipt)"
                )

                # ── Action buttons (human-only status transitions)
                st.markdown("**Action:**")
                btn_cols = st.columns(4)

                def _apply_status(new_status: str) -> None:
                    updated = set_status_human(row, new_status, notes_input)
                    idx = cands_df.index[cands_df["candidate_id"] == selected_cid][0]
                    for k, v in updated.items():
                        cands_df.at[idx, k] = v
                    _save_candidates(cands_df)
                    st.rerun()

                with btn_cols[0]:
                    if st.button("✓ Verified", type="primary", use_container_width=True,
                                 disabled=bool(missing_fields)):
                        _apply_status("verified")

                with btn_cols[1]:
                    if st.button("~ Needs evidence", use_container_width=True):
                        _apply_status("needs_more_evidence")

                with btn_cols[2]:
                    if st.button("✗ Reject", use_container_width=True):
                        _apply_status("rejected")

                with btn_cols[3]:
                    if st.button("⊘ Duplicate", use_container_width=True):
                        _apply_status("duplicate")

                if missing_fields:
                    st.caption("Verify button is disabled until all required fields are present: " + ", ".join(missing_fields))

                st.divider()

                # ── Send to bundle generator (only if eligible)
                if can_become_bundle(row):
                    if st.button("→ Send to Bundle Generator", type="primary"):
                        from saveloop.bundles.generator import generate_bundles
                        from saveloop.bundles.writer import save_bundles
                        one_df = pd.DataFrame([row])
                        bundles = generate_bundles(one_df)
                        if not bundles.empty:
                            existing_bundles = _load_csv(bundles_path)
                            combined = pd.concat([existing_bundles, bundles], ignore_index=True).drop_duplicates(subset=["bundle_id"])
                            combined.to_csv(bundles_path, index=False)
                            st.success(f"Added {len(bundles)} bundle(s) to content_bundles.csv.")
                        else:
                            st.warning("No bundles generated — check candidate fields.")
                else:
                    st.info("This candidate must be **Verified** before it can enter bundle generation.")

        st.divider()

        # ── Triage helper (Gemini pre-fill)
        with st.expander("AI triage helper — pre-fill fields from raw text"):
            st.caption("Gemini will suggest product, retailer, claimed_change etc. You still verify manually.")
            triage_cid = st.selectbox(
                "Pick a candidate to triage",
                options=cands_df["candidate_id"].tolist(),
                key="triage_select",
            )
            if st.button("Run triage") and triage_cid:
                row_t = cands_df[cands_df["candidate_id"] == triage_cid].iloc[0].to_dict()
                from saveloop.triage.extractor import extract_candidate_fields
                with st.spinner("Asking Gemini…"):
                    suggestions = extract_candidate_fields(str(row_t.get("raw_text", "")))
                if suggestions:
                    st.json(suggestions)
                    if st.button("Apply suggestions to candidate"):
                        idx_t = cands_df.index[cands_df["candidate_id"] == triage_cid][0]
                        for k, v in suggestions.items():
                            if k in cands_df.columns and v:
                                cands_df.at[idx_t, k] = v
                        _save_candidates(cands_df)
                        st.success("Applied. Review before verifying.")
                        st.rerun()
                else:
                    st.info("No suggestions returned (Gemini unavailable or extraction failed).")

        # ── Community submissions intake
        with st.expander("Import community submissions (Google Form CSV)"):
            st.caption("Drop the CSV export into `data/raw/submissions.csv`, then click Import.")
            if st.button("Import submissions"):
                from saveloop.integrations.submissions import ingest_submissions
                n = ingest_submissions()
                if n:
                    st.success(f"Imported {n} new submission(s) as pending_review candidates.")
                    st.rerun()
                else:
                    st.info("No new submissions found (file missing or all already imported).")


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED — single post, bundle board, trends
# ═══════════════════════════════════════════════════════════════════════════════

with advanced_tab:
    adv_cands, adv_bundles, adv_single = st.tabs(["Candidates", "Bundle Board", "Single Post"])

    with adv_cands:
        st.subheader("All candidates")
        cands_all = _load_csv(candidates_path)
        if cands_all.empty:
            st.info("No candidates yet. Use 'Fetch fresh signals' or import submissions.")
        else:
            status_filter = st.multiselect(
                "Filter by status",
                options=["new", "pending_review", "verified", "needs_more_evidence", "rejected", "duplicate", "posted"],
                default=["new", "pending_review", "verified"],
            )
            filtered = cands_all[cands_all["status"].isin(status_filter)] if status_filter else cands_all
            st.dataframe(filtered, use_container_width=True, hide_index=True)

    with adv_bundles:
        st.subheader("Bundle board")
        bundles_df_adv = _load_csv(bundles_path)
        if bundles_df_adv.empty:
            st.info("No bundles yet. Use the Verification Board to send verified candidates to bundles.")
        else:
            status_options = ["draft", "shortlisted", "selected", "posted", "archived"]
            show_cols = [c for c in [
                "bundle_id", "bundle_title", "pillar", "trend_keyword",
                "format", "posting_window", "priority_score", "verification_label",
                "status", "notes",
            ] if c in bundles_df_adv.columns]
            editable = bundles_df_adv[show_cols].copy()
            edited = st.data_editor(
                editable, use_container_width=True, hide_index=True,
                column_config={"status": st.column_config.SelectboxColumn(options=status_options)},
                key="bundle_editor",
            )
            if st.button("Save changes"):
                merged = bundles_df_adv.drop(
                    columns=[c for c in ["status", "notes"] if c in bundles_df_adv.columns]
                ).merge(edited[["bundle_id", "status", "notes"]], on="bundle_id", how="left")
                merged.to_csv(bundles_path, index=False)
                st.success("Saved.")
                st.rerun()

    with adv_single:
        st.subheader("Single post studio")
        bundles_df_sp = _load_csv(bundles_path)
        if bundles_df_sp.empty:
            st.info("No bundles available. Send verified candidates to the bundle generator first.")
        else:
            this_week_kws = _this_week_keywords()

            def _label(row: pd.Series) -> str:
                kw   = str(row.get("trend_keyword", "")).lower()
                flag = " ⚠ done this week" if kw in this_week_kws else ""
                v    = f" [{row.get('verification_label', '')}]" if row.get("verification_label") else ""
                return f"{row['bundle_title']} ({row.get('pillar','')}, {row['priority_score']:.2f}){v}{flag}"

            opts        = bundles_df_sp.sort_values("priority_score", ascending=False)
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
                            st.session_state["_single_zip"]      = zb
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

    history = all_history()
    if history:
        st.markdown("#### Post history (all weeks)")
        rows = []
        for entry in reversed(history):
            for post in entry.get("posts", []):
                rows.append({
                    "week":      entry.get("week"),
                    "palette":   entry.get("palette"),
                    "day":       post.get("post_day"),
                    "topic":     post.get("bundle_title"),
                    "keyword":   post.get("trend_keyword"),
                    "pillar":    post.get("pillar"),
                    "hook":      post.get("hook"),
                    "published": "✓" if post.get("published") else "—",
                })
        hist_df = pd.DataFrame(rows)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

        with st.expander("Mark posts as published"):
            all_topics = [r["topic"] for r in rows if r["published"] == "—"]
            to_mark    = st.multiselect("Select posts you actually published", all_topics)
            if st.button("Mark published") and to_mark:
                for title in to_mark:
                    mark_posted(title)
                st.success("Updated.")
                st.rerun()

        all_keywords = [r["keyword"] for r in rows]
        st.markdown(
            f"**Topics covered so far ({len(all_keywords)}):** "
            + "  ".join(f"`{k}`" for k in sorted(set(all_keywords)))
        )
        st.divider()

    if summary_path.exists():
        st.markdown(summary_path.read_text(encoding="utf-8"))
    else:
        st.info("Run `python -m saveloop.cli report` to generate a performance summary.")

    if not posts_df.empty:
        cols = [c for c in [
            "post_id", "bundle_id", "pattern", "aesthetic_tags",
            "J_score", "engagement_rate", "win_flag",
        ] if c in posts_df.columns]
        st.dataframe(posts_df[cols], use_container_width=True, hide_index=True)
