from __future__ import annotations

import argparse

from saveloop.bundles.generator import generate_bundles
from saveloop.bundles.writer import save_bundles
from saveloop.generation.post_assembler import build_post_plan, save_post_plan
from saveloop.io.loaders import load_posts_log
from saveloop.reporting.markdown import run_analysis_pipeline, write_summary
from saveloop.trends.fetchers import fetch_fresh_trends, load_trends
from saveloop.trends.scoring import score_trends


def _run_validate() -> None:
    df = load_posts_log()
    print(f"Posts log validated successfully with {len(df)} rows.")


def _run_analyze() -> None:
    outputs = run_analysis_pipeline()
    print("Analysis complete.")
    for name, path in outputs.items():
        print(f"- {name}: {path}")


def _run_report() -> None:
    path = write_summary()
    print(f"Wrote summary to: {path}")


def _run_recommend() -> None:
    path = write_summary()
    print(f"Updated recommendation in: {path}")


def _run_trends(fetch: bool = False) -> None:
    if fetch:
        print("Fetching fresh trends from Google Trends and Reddit…")
        trends_df = score_trends(fetch_fresh_trends())
        print(f"Fetched and saved {len(trends_df)} trend rows.")
    else:
        trends_df = score_trends(load_trends())
        print(f"Loaded {len(trends_df)} trend rows.")
    if not trends_df.empty:
        preview = trends_df[["keyword", "theme", "trend_score"]].to_string(index=False)
        print(preview)


def _run_bundles() -> None:
    trends_df = score_trends(load_trends())
    bundles_df = generate_bundles(trends_df)
    out_path = save_bundles(bundles_df)
    print(f"Generated {len(bundles_df)} content bundles.")
    print(f"- bundles: {out_path}")


def _run_generate() -> None:
    from pathlib import Path
    import pandas as pd

    bundles_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "content_bundles.csv"
    if not bundles_path.exists():
        print("No bundle file found. Run `python -m saveloop.cli bundles` first.")
        return

    bundles_df = pd.read_csv(bundles_path)
    if bundles_df.empty:
        print("Bundle file is empty. Generate bundles first.")
        return

    selected = bundles_df[bundles_df["status"] == "selected"]
    if selected.empty:
        selected = bundles_df.sort_values(["priority_score", "status"], ascending=[False, True]).head(1)

    row = selected.iloc[0].to_dict()
    plan = build_post_plan(row)
    out_path = save_post_plan(plan)
    print(f"Generated post plan for bundle: {row['bundle_id']}")
    print(f"- post_plan: {out_path}")


def _run_full() -> None:
    _run_validate()
    _run_analyze()
    _run_report()


def main() -> None:
    parser = argparse.ArgumentParser(description="saveloop CLI")
    parser.add_argument(
        "command",
        choices=["validate", "analyze", "report", "recommend", "run", "trends", "bundles", "generate"],
        help="Pipeline step to run",
    )
    parser.add_argument("--fetch", action="store_true", help="Fetch fresh trends from Google Trends and Reddit (use with 'trends')")
    args = parser.parse_args()

    if args.command == "validate":
        _run_validate()
    elif args.command == "analyze":
        _run_analyze()
    elif args.command == "report":
        _run_report()
    elif args.command == "recommend":
        _run_recommend()
    elif args.command == "run":
        _run_full()
    elif args.command == "trends":
        _run_trends(fetch=getattr(args, "fetch", False))
    elif args.command == "bundles":
        _run_bundles()
    elif args.command == "generate":
        _run_generate()


if __name__ == "__main__":
    main()
