from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from saveloop.config import project_paths
from saveloop.io.validation import NUMERIC_COLUMNS, REQUIRED_POST_COLUMNS, validate_required_columns

# ── Candidate columns ─────────────────────────────────────────────────────────

CANDIDATE_COLUMNS = [
    "candidate_id", "source", "raw_text", "theme", "product", "retailer",
    "claimed_change", "old_value", "new_value", "unit_price_before",
    "unit_price_after", "verified_increase_pct", "source_url", "submitted_by",
    "observed_at", "status", "verification_label", "verification_notes", "confidence",
]

# Themes where verification_required is False — eligible at any status
_VERIFICATION_NOT_REQUIRED_THEMES = {"honest_meal"}


# ── Posts log ─────────────────────────────────────────────────────────────────

def _coerce_float(value: object) -> float:
    try:
        if value is None:
            return math.nan
        text = str(value).strip()
        if text == "":
            return math.nan
        return float(text)
    except Exception:
        return math.nan


def load_posts_log(path: Path | None = None) -> pd.DataFrame:
    paths = project_paths()
    path = path or (paths["raw_data_dir"] / "posts_log.csv")
    if not path.exists():
        raise SystemExit(f"Posts log not found: {path}")

    df = pd.read_csv(path)
    missing = validate_required_columns(df, REQUIRED_POST_COLUMNS)
    if missing:
        raise SystemExit(f"Missing required columns in posts log: {', '.join(missing)}")

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = df[column].apply(_coerce_float)

    return df


def load_csv_if_exists(filename: str) -> pd.DataFrame:
    path = project_paths()["raw_data_dir"] / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# ── Candidates ────────────────────────────────────────────────────────────────

def load_candidates(path: Path | None = None) -> pd.DataFrame:
    """Load the full candidates store. Returns an empty DataFrame with correct columns if absent."""
    paths = project_paths()
    path = path or (paths["raw_data_dir"] / "candidates.csv")
    if not path.exists():
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)

    df = pd.read_csv(path)

    # Ensure all expected columns exist
    for col in CANDIDATE_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col not in ("unit_price_before", "unit_price_after",
                                        "verified_increase_pct", "confidence") else None

    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)
    for col in ["status", "theme", "source", "raw_text", "verification_label",
                "verification_notes", "candidate_id"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    return df


def load_verified_candidates(path: Path | None = None) -> pd.DataFrame:
    """
    Return candidates eligible for bundle generation:
    - status == 'verified', OR
    - theme in VERIFICATION_NOT_REQUIRED_THEMES (e.g. honest_meal)
    """
    df = load_candidates(path)
    if df.empty:
        return df

    mask = (df["status"] == "verified") | df["theme"].isin(_VERIFICATION_NOT_REQUIRED_THEMES)
    return df[mask].reset_index(drop=True)
