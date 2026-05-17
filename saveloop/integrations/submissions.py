from __future__ import annotations

"""
Community submission intake.

Reads a Google Sheets CSV export (from a Google Form) into the candidates store.
Default path: data/raw/submissions.csv (configurable via config.yaml integrations.submissions_csv).
"""

import hashlib
from pathlib import Path

import pandas as pd

from saveloop.config import project_paths
from datetime import date

# Maps Google Form column headers → Candidate field names
_SUBMISSION_COLUMN_MAP = {
    "Product name": "product",
    "Retailer": "retailer",
    "What changed": "claimed_change",
    "Old size/price": "old_value",
    "New size/price": "new_value",
    "Location/date": "verification_notes",
    "Contact (optional)": "_contact_raw",
}


def _default_submissions_path() -> Path:
    from saveloop.config import load_settings
    settings = load_settings()
    rel = settings.get("integrations", {}).get("submissions_csv", "data/raw/submissions.csv")
    return project_paths()["raw_data_dir"].parent.parent / rel


def _anon_token(contact: str) -> str:
    contact = str(contact).strip()
    if not contact or contact in ("", "None", "nan"):
        return ""
    return "sub_" + hashlib.md5(contact.encode()).hexdigest()[:8]


def _candidate_id(raw_text: str) -> str:
    return "sub_" + hashlib.md5(f"submission:{raw_text}".encode()).hexdigest()[:10]


def load_submissions(path: Path | None = None) -> pd.DataFrame:
    """
    Load community submissions CSV and convert to candidate rows.
    Returns an empty DataFrame if the file does not exist or is empty.
    """
    path = path or _default_submissions_path()
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame()

    today = date.today().isoformat()
    candidates = []

    for _, row in df.iterrows():
        mapped: dict = {}
        for form_col, cand_col in _SUBMISSION_COLUMN_MAP.items():
            val = row.get(form_col, "")
            mapped[cand_col] = str(val).strip() if pd.notna(val) else ""

        contact_raw = mapped.pop("_contact_raw", "")
        product = mapped.get("product", "")
        claimed = mapped.get("claimed_change", "")
        raw_text = f"{product}: {claimed}".strip(": ") or str(row.to_dict())[:80]

        candidates.append({
            "candidate_id": _candidate_id(raw_text),
            "source": "submission",
            "raw_text": raw_text,
            "theme": "shrinkflation",      # default; triage extractor can refine
            "product": product,
            "retailer": mapped.get("retailer", ""),
            "claimed_change": claimed,
            "old_value": mapped.get("old_value", ""),
            "new_value": mapped.get("new_value", ""),
            "unit_price_before": None,
            "unit_price_after": None,
            "verified_increase_pct": None,
            "source_url": None,
            "submitted_by": _anon_token(contact_raw),
            "observed_at": today,
            "status": "pending_review",
            "verification_label": "reader_submitted_checking",
            "verification_notes": mapped.get("verification_notes", ""),
            "confidence": 0.0,
        })

    return pd.DataFrame(candidates)


def ingest_submissions(submissions_path: Path | None = None) -> int:
    """
    Load submissions CSV and append new rows to candidates.csv.
    Returns the count of new candidates added.
    """
    from saveloop.io.loaders import load_candidates

    submissions_df = load_submissions(submissions_path)
    if submissions_df.empty:
        return 0

    cand_path = project_paths()["raw_data_dir"] / "candidates.csv"

    try:
        existing = load_candidates(cand_path)
        existing_ids = set(existing["candidate_id"].tolist())
    except Exception:
        existing = pd.DataFrame()
        existing_ids = set()

    new_df = submissions_df[~submissions_df["candidate_id"].isin(existing_ids)]
    if new_df.empty:
        return 0

    combined = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(cand_path, index=False)
    return len(new_df)
