from __future__ import annotations

"""
AI-assisted triage helper.

Uses Gemini to pre-fill structured candidate fields from raw_text.
This is a read-only suggestion layer — it never sets status.
The HUMAN_ONLY_STATUSES enforcement in verification/checker.py ensures
no automated process can verify a candidate.
"""

import json
import os


def extract_candidate_fields(raw_text: str) -> dict:
    """
    Suggest structured field values for a candidate based on its raw_text.

    Returns a dict with zero or more of:
        product, retailer, claimed_change, old_value, new_value, theme

    Returns an empty dict if Gemini is unavailable or extraction fails.
    Does NOT return or suggest a 'status' field.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {}

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""Extract structured fields from this consumer complaint or report.
Return JSON only — no markdown, no explanation.

Text: {raw_text[:500]}

Extract these fields (use null if not present):
- product: product or service name (string or null)
- retailer: retailer or company name (string or null)
- claimed_change: what changed, e.g. "box reduced from 400g to 350g" (string or null)
- old_value: price or size before the change (string or null)
- new_value: price or size after the change (string or null)
- theme: one of — shrinkflation, fake_deals, single_person, subscriptions, honest_meal (string)

JSON:"""

        resp = model.generate_content(prompt)
        text = resp.text.strip()

        # Strip markdown code fences if present
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else text
            if text.startswith("json"):
                text = text[4:]

        result = json.loads(text.strip())

        # Ensure 'status' is never returned — defensive strip
        result.pop("status", None)
        result.pop("verification_label", None)
        result.pop("confidence", None)

        return {k: v for k, v in result.items() if v is not None}

    except Exception:
        return {}
