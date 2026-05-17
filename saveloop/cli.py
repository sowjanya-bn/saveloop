from __future__ import annotations

import argparse

from saveloop.bundles.generator import generate_bundles
from saveloop.bundles.writer import save_bundles
from saveloop.generation.post_assembler import build_post_plan, save_post_plan
from saveloop.io.loaders import load_posts_log, load_candidates, load_verified_candidates
from saveloop.reporting.markdown import run_analysis_pipeline, write_summary
from saveloop.trends.fetchers import fetch_fresh_trends, load_trends
from saveloop.trends.scoring import score_trends

# Statuses that cannot be set from CLI — Streamlit UI only
_CLI_BLOCKED_STATUSES = {"verified", "rejected", "needs_more_evidence", "duplicate"}


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
        print("Fetching fresh signals from Google Trends, Reddit, and RSS…")
        trends_df = score_trends(fetch_fresh_trends())
        print(f"Fetched {len(trends_df)} signals. New candidates added to candidates.csv.")
    else:
        trends_df = score_trends(load_trends())
        print(f"Loaded {len(trends_df)} trend rows.")
    if not trends_df.empty:
        preview = trends_df[["keyword", "theme", "trend_score"]].to_string(index=False)
        print(preview)


def _run_bundles() -> None:
    candidates_df = load_verified_candidates()
    if candidates_df.empty:
        print("No verified candidates found in candidates.csv.")
        print("Use the Streamlit Verification Board to verify candidates,")
        print("or run 'python -m saveloop.cli trends --fetch' to import fresh signals.")
        return
    bundles_df = generate_bundles(candidates_df)
    out_path   = save_bundles(bundles_df)
    print(f"Generated {len(bundles_df)} content bundles from {len(candidates_df)} verified candidates.")
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

    row      = selected.iloc[0].to_dict()
    plan     = build_post_plan(row)
    out_path = save_post_plan(plan)
    print(f"Generated post plan for bundle: {row['bundle_id']}")
    print(f"- post_plan: {out_path}")


def _run_verify(args: argparse.Namespace) -> None:
    import pandas as pd
    from saveloop.config import project_paths
    from saveloop.verification.checker import validate_fields, set_status_automated

    cand_path = project_paths()["raw_data_dir"] / "candidates.csv"

    if args.list:
        df = load_candidates()
        pending = df[df["status"].isin(["new", "pending_review"])]
        if pending.empty:
            print("No pending candidates.")
            return
        print(f"{'ID':<14} {'Status':<16} {'Theme':<16} {'Product':<24} {'Missing fields'}")
        print("-" * 90)
        for _, row in pending.iterrows():
            missing = validate_fields(row.to_dict())
            missing_str = ", ".join(missing) if missing else "—"
            product = str(row.get("product") or row.get("raw_text", ""))[:23]
            print(
                f"{str(row['candidate_id']):<14} "
                f"{str(row['status']):<16} "
                f"{str(row['theme']):<16} "
                f"{product:<24} "
                f"{missing_str}"
            )
        return

    if args.candidate:
        if not args.status:
            print("--status is required when using --candidate.")
            return

        if args.status in _CLI_BLOCKED_STATUSES:
            print(
                f"Error: status '{args.status}' can only be set via the Streamlit Verification Board."
            )
            print(f"Blocked statuses: {', '.join(sorted(_CLI_BLOCKED_STATUSES))}")
            return

        df = load_candidates()
        mask = df["candidate_id"] == args.candidate
        if not mask.any():
            print(f"Candidate not found: {args.candidate}")
            return

        idx = df.index[mask][0]
        try:
            updated = set_status_automated(df.loc[idx].to_dict(), args.status)
        except ValueError as exc:
            print(f"Error: {exc}")
            return

        if args.notes:
            existing = str(updated.get("verification_notes", "")).strip()
            updated["verification_notes"] = f"{existing}\n{args.notes}".strip() if existing else args.notes

        for k, v in updated.items():
            df.at[idx, k] = v

        df.to_csv(cand_path, index=False)
        print(f"Candidate {args.candidate} updated: status → {args.status}")
        return

    print("Use --list to view pending candidates, or --candidate ID --status STATUS to update.")


def _run_full() -> None:
    _run_validate()
    _run_analyze()
    _run_report()


def main() -> None:
    parser = argparse.ArgumentParser(description="saveloop CLI")
    parser.add_argument(
        "command",
        choices=["validate", "analyze", "report", "recommend", "run",
                 "trends", "bundles", "generate", "verify"],
        help="Pipeline step to run",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch fresh signals (use with 'trends')",
    )
    # verify sub-options
    parser.add_argument("--list",      action="store_true", help="List pending candidates (use with 'verify')")
    parser.add_argument("--candidate", metavar="ID",        help="Candidate ID to update (use with 'verify')")
    parser.add_argument("--status",    metavar="STATUS",    help="New status (use with 'verify --candidate')")
    parser.add_argument("--notes",     metavar="TEXT",      help="Verification notes (use with 'verify --candidate')")
    # submissions sub-option
    parser.add_argument("--path",      metavar="FILE",      help="Override default CSV path (use with future 'submissions' command)")

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
        _run_trends(fetch=args.fetch)
    elif args.command == "bundles":
        _run_bundles()
    elif args.command == "generate":
        _run_generate()
    elif args.command == "verify":
        _run_verify(args)


if __name__ == "__main__":
    main()
