from __future__ import annotations

import argparse

from saveloop.io.loaders import load_posts_log
from saveloop.reporting.markdown import run_analysis_pipeline, write_summary


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


def _run_full() -> None:
    _run_validate()
    _run_analyze()
    _run_report()


def main() -> None:
    parser = argparse.ArgumentParser(description="saveloop CLI")
    parser.add_argument(
        "command",
        choices=["validate", "analyze", "report", "recommend", "run"],
        help="Pipeline step to run",
    )
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


if __name__ == "__main__":
    main()
