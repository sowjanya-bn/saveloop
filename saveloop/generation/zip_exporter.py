from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any


def _format_caption(plan: dict[str, Any]) -> str:
    caption = plan.get("caption", "").strip()
    cta = plan.get("closing_cta", "").strip()
    # Avoid duplicating the CTA if the caption already ends with it
    if cta and not caption.rstrip(".").endswith(cta.rstrip(".")):
        caption = f"{caption}\n\n{cta}"
    return caption


def _format_hashtags(plan: dict[str, Any]) -> str:
    raw = str(plan.get("hashtags") or "")
    tags = [t.strip() for t in raw.split(",") if t.strip()]
    return "\n".join(tags)


def build_instagram_zip(
    slide_paths: list[Path],
    plan: dict[str, Any],
) -> bytes:
    """
    Pack carousel PNGs + caption.txt + hashtags.txt into an in-memory zip.
    Returns raw zip bytes suitable for st.download_button.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in slide_paths:
            zf.write(path, arcname=path.name)
        zf.writestr("caption.txt", _format_caption(plan))
        zf.writestr("hashtags.txt", _format_hashtags(plan))
    return buf.getvalue()
