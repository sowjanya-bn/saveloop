from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from saveloop.generation.image_generator import generate_image_prompt
from saveloop.generation.local_image_provider import generate_local_image


def _gemini_generate_image(
    image_prompt: str,
    model: str,
    image_path: Path,
) -> tuple[bool, str | None]:
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return False, f"google-genai package not installed: {exc}"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False, "GEMINI_API_KEY not set"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=[image_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["Image"],
                image_config=types.ImageConfig(aspect_ratio="1:1"),
            ),
        )

        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    image_path.write_bytes(base64.b64decode(inline_data.data))
                    return True, None

        return False, "No image data returned by Gemini"
    except Exception as exc:
        return False, str(exc)


def maybe_generate_image(
    bundle: dict[str, Any],
    copy: dict[str, Any],
    generate_asset: bool = False,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    prompt_payload = generate_image_prompt(bundle)
    image_prompt = prompt_payload["image_prompt"]
    alt_text = prompt_payload["alt_text"]

    if not generate_asset:
        return {
            "image_prompt": image_prompt,
            "alt_text": alt_text,
            "image_path": None,
            "image_generated": False,
            "image_backend": "prompt_only",
        }

    output_dir = output_dir or Path(__file__).resolve().parents[2] / "data" / "generated" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{bundle.get('bundle_id', 'bundle')}.png"

    backend = os.getenv("SAVELOOP_IMAGE_BACKEND", "local").strip().lower()
    model = os.getenv("SAVELOOP_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

    if backend == "gemini":
        ok, error = _gemini_generate_image(image_prompt=image_prompt, model=model, image_path=image_path)
        if ok:
            return {
                "image_prompt": image_prompt,
                "alt_text": alt_text,
                "image_path": str(image_path),
                "image_generated": True,
                "image_backend": "gemini",
            }
        local_result = generate_local_image(bundle, copy, image_prompt, alt_text, output_dir)
        local_result["image_error"] = f"Gemini fallback used: {error}"
        return local_result

    return generate_local_image(bundle, copy, image_prompt, alt_text, output_dir)
