"""
Command line for saveloop.

Usage:
  python -m saveloop.cli analyze

This runs the metric computation and writes a weekly summary.
"""
import argparse
from . import reporting

def main():
    ap = argparse.ArgumentParser(description="saveloop CLI")
    ap.add_argument("command", choices=["analyze"], help="What to run")
    args = ap.parse_args()
    if args.command == "analyze":
        out = reporting.write_summary()
        print(f"Wrote summary to: {out}")

if __name__ == "__main__":
    main()
