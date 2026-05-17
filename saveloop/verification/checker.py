from __future__ import annotations

from typing import Optional

# These statuses may only be written by a human via the Streamlit Verification Board.
# No automated function in this module may set them.
HUMAN_ONLY_STATUSES = {"verified", "rejected", "needs_more_evidence", "duplicate"}

# Allowed automated transitions (non-human)
_AUTOMATED_TRANSITIONS: dict[str, set[str]] = {
    "new": {"pending_review"},
    "pending_review": set(),   # terminal until human acts
    "verified": {"posted"},
    "needs_more_evidence": set(),
    "rejected": set(),
    "duplicate": set(),
    "posted": set(),
}

# Fields that must be non-empty for a candidate to pass specificity check
REQUIRED_FIELDS_FOR_VERIFICATION = ["product", "retailer", "claimed_change"]

# Themes where verification is not required — candidates can become bundles at any status
VERIFICATION_NOT_REQUIRED_THEMES = {"honest_meal"}


def validate_fields(candidate: dict) -> list[str]:
    """
    Return a list of field names that are missing or empty.
    An empty list means the candidate passes the specificity check.
    """
    missing = []
    for f in REQUIRED_FIELDS_FOR_VERIFICATION:
        val = candidate.get(f)
        if val is None or str(val).strip() in ("", "None", "nan"):
            missing.append(f)
    return missing


def calculate_unit_price_increase(candidate: dict) -> Optional[float]:
    """
    Compute the percentage increase between unit_price_before and unit_price_after.
    Returns None if either value is absent or zero.
    """
    try:
        before = float(candidate.get("unit_price_before") or 0)
        after = float(candidate.get("unit_price_after") or 0)
        if before > 0 and after > 0:
            return round((after - before) / before * 100, 2)
    except (TypeError, ValueError):
        pass
    return None


def can_become_bundle(candidate: dict) -> bool:
    """
    Return True if the candidate is eligible to enter bundle generation.

    Rules:
    - Candidates with a verification-not-required theme (e.g. honest_meal) are always eligible.
    - All other candidates must have status == 'verified'.
    """
    theme = str(candidate.get("theme", "")).strip().lower()
    if theme in VERIFICATION_NOT_REQUIRED_THEMES:
        return True
    return candidate.get("status") == "verified"


def set_status_automated(candidate: dict, new_status: str) -> dict:
    """
    Apply a status transition via automated code (CLI, fetchers, intake).
    Raises ValueError if the target status is in HUMAN_ONLY_STATUSES or
    the transition is not permitted from the current status.
    """
    if new_status in HUMAN_ONLY_STATUSES:
        raise ValueError(
            f"Status '{new_status}' is in HUMAN_ONLY_STATUSES and cannot be set "
            "by automated processes. Use the Streamlit Verification Board."
        )
    current = str(candidate.get("status", "new"))
    allowed = _AUTOMATED_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        allowed_str = ", ".join(sorted(allowed)) if allowed else "none (terminal state)"
        raise ValueError(
            f"Invalid automated transition: {current!r} → {new_status!r}. "
            f"Allowed from '{current}': {allowed_str}"
        )
    return {**candidate, "status": new_status}


def set_status_human(candidate: dict, new_status: str, notes: str = "") -> dict:
    """
    Apply a status transition via human action (Streamlit UI only).
    Permits HUMAN_ONLY_STATUSES in addition to automated ones.
    Appends notes to verification_notes if provided.
    """
    all_valid = HUMAN_ONLY_STATUSES | {"pending_review", "posted", "new"}
    if new_status not in all_valid:
        raise ValueError(f"Unknown status: {new_status!r}")
    updated = {**candidate, "status": new_status}
    if new_status == "verified":
        updated["verification_label"] = "verified"
    elif new_status == "needs_more_evidence":
        updated["verification_label"] = "interesting_unconfirmed"
    if notes:
        existing = str(updated.get("verification_notes", "")).strip()
        updated["verification_notes"] = f"{existing}\n{notes}".strip() if existing else notes
    return updated
