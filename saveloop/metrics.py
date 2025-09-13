"""
Metrics for saveloop.

This module computes rates and the save first objective J.
All formulas are documented inline so you can read them inside the project.

Fields expected in data/posts_log.csv:
- views, comments, saves, shares, profile_visits, dms_started, likes
- format to choose win thresholds
- aesthetic_tags as comma separated labels

Formulas:
- save_rate = saves ÷ views
- comment_rate = comments ÷ views
- dm_rate = dms_started ÷ profile_visits
- hook_efficiency = (saves × 1000) ÷ views
- engagement_rate = (likes + comments + saves + shares) ÷ views
- J = w_s*save_rate + w_c*comment_rate + w_d*dm_rate
  where weights come from config.yaml
"""
from __future__ import annotations
import math, re, yaml
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = ROOT / "config.yaml"
OUT = DATA / "out"

def _coerce_float(x):
    """Return float or NaN. Accepts str, int, float, or empty."""
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)) or str(x).strip() == "":
            return math.nan
        return float(str(x).strip())
    except Exception:
        return math.nan

def _safe_div(a, b):
    """Return a / b or NaN if input is missing or b is zero."""
    a = _coerce_float(a); b = _coerce_float(b)
    if pd.isna(a) or pd.isna(b) or b == 0:
        return math.nan
    return a / b

def _parse_afs(note: str):
    """
    Parse the aesthetic rubric from a free text note.
    Expected format: 'AFS: x,x,x,x,x,x,x,x,x'
    Returns the mean or NaN.
    """
    if not isinstance(note, str):
        return math.nan
    m = re.search(r"AFS:\s*([0-5](?:\s*,\s*[0-5]){8})", note)
    if not m:
        return math.nan
    nums = [int(x.strip()) for x in m.group(1).split(",")]
    if len(nums) != 9:
        return math.nan
    return sum(nums) / 9.0

def load_cfg() -> dict:
    """Load YAML config with weights and thresholds."""
    with open(CFG, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def compute_all():
    """
    Read data/posts_log.csv, compute metrics and J, write enriched CSVs.
    Returns the output directory path.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    log_path = DATA / "posts_log.csv"
    if not log_path.exists():
        raise SystemExit("data/posts_log.csv not found")

    df = pd.read_csv(log_path)

    # Coerce numeric fields
    for col in ["views","reach","likes","comments","saves","shares","profile_visits","follows","avg_view_duration_s","replays","dms_started"]:
        if col in df.columns:
            df[col] = df[col].apply(_coerce_float)

    # Rates
    df["save_rate"] = df.apply(lambda r: _safe_div(r.get("saves"), r.get("views")), axis=1)
    df["comment_rate"] = df.apply(lambda r: _safe_div(r.get("comments"), r.get("views")), axis=1)
    df["dm_rate"] = df.apply(lambda r: _safe_div(r.get("dms_started"), r.get("profile_visits")), axis=1)
    df["hook_efficiency"] = df.apply(lambda r: (r.get("saves", 0)*1000.0/r.get("views")) if r.get("views") not in (None, 0) and not math.isnan(r.get("views")) else math.nan, axis=1)
    df["engagement_rate"] = df.apply(lambda r: _safe_div((r.get("likes",0) + r.get("comments",0) + r.get("saves",0) + r.get("shares",0)), r.get("views")), axis=1)

    # Aesthetic rubric mean
    df["afs_mean"] = df.get("note", pd.Series([math.nan]*len(df))).apply(_parse_afs)

    # J
    cfg = load_cfg()
    w = cfg.get("objective", {}).get("weights", {"save_rate":0.6, "comment_rate":0.3, "dm_rate":0.1})
    df["J_score"] = (w.get("save_rate",0)*df["save_rate"]
                     + w.get("comment_rate",0)*df["comment_rate"]
                     + w.get("dm_rate",0)*df["dm_rate"])

    # Win flags
    reel_th = cfg.get("thresholds", {}).get("reel_engagement_win", 0.005)
    car_th = cfg.get("thresholds", {}).get("carousel_engagement_win", 0.0055)
    def _win(row):
        er = row["engagement_rate"]
        if pd.isna(er): return ""
        fmt = str(row.get("format","")).lower()
        if fmt.startswith("carousel"):
            return "win" if er >= car_th else ""
        return "win" if er >= reel_th else ""
    df["win_flag"] = df.apply(_win, axis=1)

    # Tag performance
    def _split_tags(x):
        if not isinstance(x, str): return []
        return [t.strip() for t in x.split(",") if t.strip()]
    df["__tags_list"] = df.get("aesthetic_tags", pd.Series([""]*len(df))).apply(_split_tags)

    tag_rows = []
    for _, row in df.iterrows():
        for t in row["__tags_list"]:
            tag_rows.append({"tag": t, "J_score": row["J_score"], "engagement_rate": row["engagement_rate"]})
    tag_df = pd.DataFrame(tag_rows)
    if not tag_df.empty:
        tag_perf = tag_df.groupby("tag").agg(count=("J_score","count"),
                                             J_mean=("J_score","mean"),
                                             ER_mean=("engagement_rate","mean")).reset_index()
    else:
        tag_perf = pd.DataFrame(columns=["tag","count","J_mean","ER_mean"])

    # Pattern performance
    if "pattern" in df.columns:
        pat_perf = df.groupby("pattern").agg(count=("J_score","count"),
                                             J_mean=("J_score","mean"),
                                             ER_mean=("engagement_rate","mean")).reset_index()
    else:
        pat_perf = pd.DataFrame(columns=["pattern","count","J_mean","ER_mean"])

    # Outputs
    df.drop(columns=["__tags_list"], errors="ignore").to_csv(OUT / "posts_log_with_metrics.csv", index=False)
    tag_perf.to_csv(OUT / "tag_performance.csv", index=False)
    pat_perf.to_csv(OUT / "pattern_performance.csv", index=False)

    return OUT
