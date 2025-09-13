"""
Simple reporting for saveloop.

Writes a weekly_summary.md that shows mean J, best post, count of wins
and one suggestion. The suggestion is based on the best tag seen at least twice.
If there are no wins it also suggests a timing test.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .metrics import compute_all, load_cfg

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "out"

def write_summary():
    """Compute metrics, then write a short markdown summary with one next step."""
    out_dir = compute_all()
    df = pd.read_csv(out_dir / "posts_log_with_metrics.csv")

    lines = []
    lines.append("# Weekly Summary\n")
    if not df["J_score"].dropna().empty:
        lines.append(f"- Posts analysed: {len(df)}")
        lines.append(f"- Mean J: {df['J_score'].mean():.4f}")
        best_idx = df["J_score"].idxmax() if not df["J_score"].dropna().empty else None
        if best_idx is not None:
            lines.append(f"- Best J: {df.loc[best_idx, 'J_score']:.4f} (post: {df.loc[best_idx, 'post_id']})")
    wins = df[df["win_flag"]=="win"]
    lines.append(f"- Wins this week: {len(wins)}")

    # Suggestion
    suggestion = "Keep one control post. Change one aesthetic lever and one timing lever next week."
    tag_perf_path = out_dir / "tag_performance.csv"
    if tag_perf_path.exists():
        tag_perf = pd.read_csv(tag_perf_path)
        tag_perf2 = tag_perf[tag_perf["count"]>=2].sort_values("J_mean", ascending=False)
        if not tag_perf2.empty:
            suggestion = f"Double down on {tag_perf2.iloc[0]['tag']}. Test steam vs text first on Sunday."
    if wins.empty:
        suggestion += " No wins yet. Also try posting time plus or minus 60 minutes."

    lines.append("")
    lines.append("**Suggestion:** " + suggestion)

    from .metrics import load_cfg
    cfg = load_cfg()
    fname = cfg.get("reporting", {}).get("summary_filename", "weekly_summary.md")
    (out_dir / fname).write_text("\n".join(lines), encoding="utf-8")
    return out_dir / fname
