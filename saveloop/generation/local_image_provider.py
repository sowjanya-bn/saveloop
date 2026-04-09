from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value).strip("_") or "bundle"


def _make_output_path(bundle: dict[str, Any], output_dir: Path, suffix: str = "png") -> Path:
    bundle_id = bundle.get("bundle_id") or bundle.get("bundle_title") or "bundle"
    return output_dir / f"{_safe_name(str(bundle_id))}.{suffix}"


def generate_prompt_card(
    bundle: dict[str, Any],
    copy: dict[str, Any],
    image_prompt: str,
    alt_text: str,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = _make_output_path(bundle, output_dir)

    width, height = 1080, 1080
    image = Image.new("RGB", (width, height), color=(247, 244, 238))
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 52)
        body_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 30)
        small_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    margin = 72
    y = 72
    title = bundle.get("bundle_title") or bundle.get("trend_keyword") or "SaveLoop"
    hook = copy.get("hook") or bundle.get("hook") or ""

    draw.rounded_rectangle((48, 48, width - 48, height - 48), radius=36, outline=(30, 30, 30), width=3)
    draw.text((margin, y), title, fill=(26, 26, 26), font=title_font)
    y += 120

    wrapped_hook = textwrap.fill(hook, width=26)
    draw.multiline_text((margin, y), wrapped_hook, fill=(50, 50, 50), font=body_font, spacing=10)
    y += 230

    chips = [
        f"Theme: {bundle.get('theme', '')}",
        f"Format: {bundle.get('format', '')}",
        f"Window: {bundle.get('posting_window', '')}",
    ]
    chip_y = y
    for chip in chips:
        draw.rounded_rectangle((margin, chip_y, width - margin, chip_y + 48), radius=18, fill=(230, 225, 218))
        draw.text((margin + 18, chip_y + 10), chip, fill=(60, 60, 60), font=small_font)
        chip_y += 64
    y = chip_y + 28

    prompt_label = "Visual direction"
    draw.text((margin, y), prompt_label, fill=(26, 26, 26), font=body_font)
    y += 52
    wrapped_prompt = textwrap.fill(image_prompt, width=52)
    draw.multiline_text((margin, y), wrapped_prompt, fill=(70, 70, 70), font=small_font, spacing=8)

    footer = alt_text or "Generated locally by SaveLoop"
    footer_y = height - 110
    draw.line((margin, footer_y - 24, width - margin, footer_y - 24), fill=(200, 194, 186), width=2)
    draw.text((margin, footer_y), footer[:120], fill=(90, 90, 90), font=small_font)

    image.save(image_path)
    return {
        "image_prompt": image_prompt,
        "alt_text": alt_text,
        "image_path": str(image_path),
        "image_generated": True,
        "image_backend": "local_prompt_card",
    }


def generate_diffusers_image(
    bundle: dict[str, Any],
    copy: dict[str, Any],
    image_prompt: str,
    alt_text: str,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = _make_output_path(bundle, output_dir)

    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except Exception as exc:
        return {
            "image_prompt": image_prompt,
            "alt_text": alt_text,
            "image_path": None,
            "image_generated": False,
            "image_backend": "local_diffusers",
            "image_error": f"Local diffusers backend unavailable: {exc}",
        }

    model_id = os.getenv("SAVELOOP_LOCAL_IMAGE_MODEL", "stabilityai/sdxl-turbo")
    steps = int(os.getenv("SAVELOOP_LOCAL_IMAGE_STEPS", "4"))
    guidance_scale = float(os.getenv("SAVELOOP_LOCAL_IMAGE_GUIDANCE", "0.0"))

    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float16
    elif torch.cuda.is_available():
        device = "cuda"
        dtype = torch.float16
    else:
        device = "cpu"
        dtype = torch.float32

    try:
        pipe = AutoPipelineForText2Image.from_pretrained(model_id, torch_dtype=dtype)
        pipe = pipe.to(device)
        result = pipe(
            prompt=image_prompt,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
        )
        image = result.images[0]
        image.save(image_path)
        return {
            "image_prompt": image_prompt,
            "alt_text": alt_text,
            "image_path": str(image_path),
            "image_generated": True,
            "image_backend": "local_diffusers",
        }
    except Exception as exc:
        return {
            "image_prompt": image_prompt,
            "alt_text": alt_text,
            "image_path": None,
            "image_generated": False,
            "image_backend": "local_diffusers",
            "image_error": f"Local diffusers generation failed: {exc}",
        }


def generate_local_image(
    bundle: dict[str, Any],
    copy: dict[str, Any],
    image_prompt: str,
    alt_text: str,
    output_dir: Path,
) -> dict[str, Any]:
    mode = os.getenv("SAVELOOP_LOCAL_IMAGE_MODE", "prompt_card").strip().lower()
    if mode == "diffusers":
        result = generate_diffusers_image(bundle, copy, image_prompt, alt_text, output_dir)
        if result.get("image_generated"):
            return result
    return generate_prompt_card(bundle, copy, image_prompt, alt_text, output_dir)
