from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from saveloop.generation.post_assembler import build_post_plan, save_post_plan

ROOT = Path(__file__).resolve().parents[2]
trends_path = ROOT / "data" / "raw" / "trends_snapshot.csv"
bundles_path = ROOT / "data" / "processed" / "content_bundles.csv"
summary_path = ROOT / "data" / "reports" / "weekly_summary.md"
posts_path = ROOT / "data" / "processed" / "posts_log_with_metrics.csv"
post_plans_path = ROOT / "data" / "processed" / "post_plans.json"

st.set_page_config(page_title="SaveLoop", layout="wide")
st.title("SaveLoop")
st.caption("Trend → bundle → generate → post → performance")


def _load_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def _load_post_plans(path: Path) -> list[dict]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            return []
    return []


trends_df = _load_csv(trends_path)
bundles_df = _load_csv(bundles_path)
posts_df = _load_csv(posts_path)
post_plans = _load_post_plans(post_plans_path)

summary_col, metric_col_1, metric_col_2, metric_col_3 = st.columns([2, 1, 1, 1])
with summary_col:
    st.subheader("Current recommendation")
    if summary_path.exists():
        summary_text = summary_path.read_text(encoding="utf-8")
        preview_lines = []
        for line in summary_text.splitlines():
            if line.startswith("## "):
                continue
            if line.strip().startswith("- What is working best right now") or line.strip().startswith("- What to do next") or line.strip().startswith("- Confidence level"):
                preview_lines.append(line)
        st.markdown("\n".join(preview_lines) if preview_lines else "Run the report workflow to generate a recommendation.")
    else:
        st.info("Run `python -m saveloop.cli report` to generate a recommendation.")
with metric_col_1:
    st.metric("Trends", len(trends_df))
with metric_col_2:
    st.metric("Bundles", len(bundles_df))
with metric_col_3:
    st.metric("Posts", len(posts_df))

trend_tab, bundle_tab, generation_tab, performance_tab = st.tabs(["Trends", "Bundle Board", "Generation Studio", "Performance"])

with trend_tab:
    st.subheader("Trend snapshot")
    if trends_df.empty:
        st.info("No trend snapshot found yet. Run the trends workflow first.")
    else:
        theme_filter = st.multiselect("Filter by theme", sorted(trends_df["theme"].dropna().unique().tolist()))
        source_filter = st.multiselect("Filter by source", sorted(trends_df["source"].dropna().unique().tolist()))
        view_df = trends_df.copy()
        if theme_filter:
            view_df = view_df[view_df["theme"].isin(theme_filter)]
        if source_filter:
            view_df = view_df[view_df["source"].isin(source_filter)]
        st.dataframe(view_df, use_container_width=True)

with bundle_tab:
    st.subheader("Bundle board")
    if bundles_df.empty:
        st.info("No bundle file found yet. Run `python -m saveloop.cli bundles` first.")
    else:
        status_options = ["draft", "shortlisted", "selected", "posted", "archived"]
        theme_filter = st.multiselect("Theme", sorted(bundles_df["theme"].dropna().unique().tolist()), key="bundle_theme")
        status_filter = st.multiselect("Status", status_options, key="bundle_status")
        view_df = bundles_df.copy()
        if theme_filter:
            view_df = view_df[view_df["theme"].isin(theme_filter)]
        if status_filter:
            view_df = view_df[view_df["status"].isin(status_filter)]

        top_candidates = view_df.sort_values("priority_score", ascending=False).head(3)
        if not top_candidates.empty:
            st.markdown("### Top candidates")
            rank_labels = ["#1 Best next post", "#2 Backup option", "#3 Exploratory option"]
            for idx, (_, row) in enumerate(top_candidates.iterrows()):
                label = rank_labels[idx] if idx < len(rank_labels) else f"#{idx + 1} Candidate"
                st.markdown(
                    f"**{label}: {row['bundle_title']}**  \n"
                    f"Trend: `{row['trend_keyword']}`  \n"
                    f"Why it matters: {row['angle']}  \n"
                    f"Suggested move: {row['hook']}  \n"
                    f"Effort: Low–Medium  \n"
                    f"Expected return: {'Medium–High' if row['priority_score'] >= 0.75 else 'Medium'}"
                )

        editable = view_df[[
            "bundle_id",
            "bundle_title",
            "theme",
            "trend_keyword",
            "format",
            "hook_style",
            "posting_window",
            "priority_score",
            "status",
            "notes",
        ]].copy()
        edited = st.data_editor(
            editable,
            use_container_width=True,
            hide_index=True,
            column_config={
                "status": st.column_config.SelectboxColumn(options=status_options),
                "priority_score": st.column_config.NumberColumn(format="%.3f"),
            },
            key="bundle_editor",
        )

        if st.button("Save bundle status updates"):
            merge_cols = ["bundle_id", "status", "notes"]
            merged = bundles_df.drop(columns=[c for c in ["status", "notes"] if c in bundles_df.columns]).merge(
                edited[merge_cols], on="bundle_id", how="left"
            )
            merged.to_csv(bundles_path, index=False)
            st.success("Bundle updates saved.")

with generation_tab:
    st.subheader("Generation studio")
    if bundles_df.empty:
        st.info("Generate bundles first to create content plans.")
    else:
        st.markdown("Create stronger copy with an LLM, and optionally generate an image asset if your API key is configured.")
        provider_col, image_col = st.columns([1, 1])
        with provider_col:
            text_provider = st.selectbox(
                "Copy generation mode",
                options=["rule_based", "gemini"],
                format_func=lambda x: "Rule-based fallback" if x == "rule_based" else "LLM-enhanced (Gemini)",
            )
        with image_col:
            generate_image_asset = st.checkbox("Generate image asset", value=False)

        if text_provider == "gemini":
            st.caption("Uses GEMINI_API_KEY and SAVELOOP_TEXT_MODEL if available. Falls back to rules if not configured.")
        if generate_image_asset:
            st.caption("Image backend is controlled by SAVELOOP_IMAGE_BACKEND. Use `local` for on-device assets or `gemini` for API generation with local fallback.")

        bundle_options = bundles_df.sort_values(["priority_score", "bundle_title"], ascending=[False, True])
        labels = {
            row["bundle_id"]: f"{row['bundle_title']} ({row['status']}, score {row['priority_score']:.2f})"
            for _, row in bundle_options.iterrows()
        }
        default_bundle_id = None
        selected_rows = bundle_options[bundle_options["status"] == "selected"]
        if not selected_rows.empty:
            default_bundle_id = selected_rows.iloc[0]["bundle_id"]
        else:
            default_bundle_id = bundle_options.iloc[0]["bundle_id"]

        selected_bundle_id = st.selectbox(
            "Choose a bundle to generate",
            options=bundle_options["bundle_id"].tolist(),
            format_func=lambda x: labels.get(x, x),
            index=bundle_options["bundle_id"].tolist().index(default_bundle_id),
        )

        selected_bundle = bundle_options[bundle_options["bundle_id"] == selected_bundle_id].iloc[0].to_dict()
        plan = build_post_plan(
            selected_bundle,
            text_provider=text_provider,
            generate_image_asset=generate_image_asset,
        )

        left, right = st.columns([1.3, 1])
        with left:
            st.markdown("### Generated post")
            st.markdown(f"**Title**: {plan['bundle_title']}")
            st.markdown(f"**Hook**: {plan['hook']}")
            st.markdown(f"**Overlay text**: {plan['overlay_text']}")
            st.markdown(f"**Tone**: {plan['tone']}")
            st.markdown(f"**Copy provider**: {plan['text_provider']}")
            st.markdown(f"**Caption**:\n\n{plan['caption']}")
            st.markdown("**Script beats**")
            for bullet in plan["script_bullets"]:
                st.markdown(f"- {bullet}")
            st.markdown(f"**Hashtags**: {plan['hashtags']}")

        with right:
            st.markdown("### Asset directions")
            st.markdown(f"**Image prompt**: {plan['image_prompt']}")
            st.markdown(f"**Music recommendation**: {plan['music_style']}")
            st.markdown(f"**Music note**: {plan['music_note']}")
            st.markdown(f"**Posting window**: {plan['posting_window']}")
            st.markdown(f"**Priority score**: {plan['priority_score']}")
            if plan.get("image_backend"):
                st.markdown(f"**Image backend**: {plan['image_backend']}")
            if plan.get("image_generated") and plan.get("image_path"):
                st.markdown("**Generated image preview**")
                st.image(plan["image_path"], use_container_width=True)
            elif plan.get("image_error"):
                st.warning(f"Image generation not completed: {plan['image_error']}")

        if st.button("Save generated post plan"):
            out_path = save_post_plan(plan)
            st.success(f"Saved generated post plan to {out_path}")

        if post_plans:
            st.markdown("### Saved post plans")
            st.dataframe(pd.DataFrame(post_plans), use_container_width=True)

with performance_tab:
    st.subheader("Performance")
    if summary_path.exists():
        st.markdown(summary_path.read_text(encoding="utf-8"))
    else:
        st.info("No summary generated yet. Run `python -m saveloop.cli report` first.")

    if not posts_df.empty:
        st.markdown("### Posted bundles")
        cols = [c for c in ["post_id", "bundle_id", "pattern", "aesthetic_tags", "J_score", "engagement_rate", "win_flag"] if c in posts_df.columns]
        st.dataframe(posts_df[cols], use_container_width=True)
