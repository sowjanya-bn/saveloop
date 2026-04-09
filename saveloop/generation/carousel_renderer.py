from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from saveloop.generation.color_schemes import PALETTES, palette_for_week

WIDTH, HEIGHT = 1080, 1080
MARGIN = 80

FONT_BOLD    = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD_LINUX    = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR_LINUX = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    for bold, regular in [(FONT_BOLD, FONT_REGULAR), (FONT_BOLD_LINUX, FONT_REGULAR_LINUX)]:
        try:
            return {
                "hero":  ImageFont.truetype(bold, 68),
                "title": ImageFont.truetype(bold, 50),
                "body":  ImageFont.truetype(regular, 34),
                "small": ImageFont.truetype(regular, 26),
                "xs":    ImageFont.truetype(regular, 22),
            }
        except Exception:
            continue
    d = ImageFont.load_default()
    return {k: d for k in ("hero", "title", "body", "small", "xs")}


def _canvas(bg: tuple) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=bg)
    return img, ImageDraw.Draw(img)


def _accent_bar(draw: ImageDraw.ImageDraw, color: tuple, top: bool = True) -> None:
    y = 0 if top else HEIGHT - 10
    draw.rectangle((0, y, WIDTH, y + 10), fill=color)


def _slide_counter(draw, fonts, current: int, total: int, color: tuple) -> None:
    label = f"{current} / {total}"
    bbox = draw.textbbox((0, 0), label, font=fonts["xs"])
    w = bbox[2] - bbox[0]
    draw.text((WIDTH - MARGIN - w, 44), label, fill=color, font=fonts["xs"])


def _wrapped_text(draw, text, font, color, x, y, max_width, line_spacing=14) -> int:
    avg_char_w = font.size // 2 if hasattr(font, "size") else 10
    wrap_chars = max(10, max_width // max(avg_char_w, 1))
    for line in textwrap.fill(text, width=wrap_chars).split("\n"):
        draw.text((x, y), line, fill=color, font=font)
        bbox = draw.textbbox((x, y), line, font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def _render_cover(plan: dict, fonts: dict, total: int, palette: dict, output_path: Path) -> Path:
    img, draw = _canvas(palette["cover_bg"])
    _accent_bar(draw, palette["accent"], top=True)
    _slide_counter(draw, fonts, 1, total, palette["muted"])

    hook = str(plan.get("hook") or plan.get("bundle_title") or "SaveLoop")
    lines = textwrap.fill(hook, width=18).split("\n")

    sample_bbox = draw.textbbox((0, 0), "Ag", font=fonts["hero"])
    line_h = (sample_bbox[3] - sample_bbox[0]) + 18
    block_h = len(lines) * line_h
    y = (HEIGHT - block_h) // 2 - 60

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fonts["hero"])
        lw = bbox[2] - bbox[0]
        draw.text(((WIDTH - lw) // 2, y), line, fill=palette["cover_text"], font=fonts["hero"])
        y += line_h

    div_y = y + 32
    draw.rectangle((MARGIN * 2, div_y, WIDTH - MARGIN * 2, div_y + 3), fill=palette["accent"])

    label = f"{plan.get('format', '')}  ·  {plan.get('theme', '')}".strip(" ·")
    if label:
        bbox = draw.textbbox((0, 0), label, font=fonts["small"])
        lw = bbox[2] - bbox[0]
        draw.text(((WIDTH - lw) // 2, div_y + 28), label, fill=palette["muted"], font=fonts["small"])

    hint = "swipe →"
    bbox = draw.textbbox((0, 0), hint, font=fonts["xs"])
    hw = bbox[2] - bbox[0]
    draw.text(((WIDTH - hw) // 2, HEIGHT - 80), hint, fill=palette["muted"], font=fonts["xs"])

    _accent_bar(draw, palette["accent"], top=False)
    img.save(output_path)
    return output_path


def _render_content_slide(slide: dict, slide_num: int, total: int, plan: dict, fonts: dict, palette: dict, output_path: Path) -> Path:
    img, draw = _canvas(palette["bg"])
    _accent_bar(draw, palette["cover_bg"], top=True)
    _slide_counter(draw, fonts, slide_num, total, palette["muted"])

    y = 140
    y = _wrapped_text(draw, str(slide.get("title", "")), fonts["title"], palette["text"], MARGIN, y, WIDTH - MARGIN * 2, line_spacing=12)

    y += 20
    draw.rectangle((MARGIN, y, MARGIN + 64, y + 5), fill=palette["accent"])
    y += 36

    y = _wrapped_text(draw, str(slide.get("body", "")), fonts["body"], palette["subtext"], MARGIN, y, WIDTH - MARGIN * 2, line_spacing=16)

    footer = str(plan.get("bundle_title") or "SaveLoop")
    draw.text((MARGIN, HEIGHT - 72), footer, fill=palette["muted"], font=fonts["xs"])

    _accent_bar(draw, palette["cover_bg"], top=False)
    img.save(output_path)
    return output_path


def _render_cta_slide(plan: dict, fonts: dict, total: int, palette: dict, output_path: Path) -> Path:
    img, draw = _canvas(palette["accent"])
    _accent_bar(draw, palette["cover_bg"], top=True)
    _slide_counter(draw, fonts, total, total, palette["muted"])

    cta = str(plan.get("closing_cta") or "Save this for later.")
    lines = textwrap.fill(cta, width=20).split("\n")

    sample_bbox = draw.textbbox((0, 0), "Ag", font=fonts["title"])
    line_h = (sample_bbox[3] - sample_bbox[0]) + 16
    block_h = len(lines) * line_h
    y = (HEIGHT - block_h) // 2 - 80

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fonts["title"])
        lw = bbox[2] - bbox[0]
        draw.text(((WIDTH - lw) // 2, y), line, fill=palette["cover_bg"], font=fonts["title"])
        y += line_h

    raw_tags = str(plan.get("hashtags") or "")
    tags = [t.strip() for t in raw_tags.split(",") if t.strip()][:5]
    if tags:
        tag_line = "  ".join(tags)
        bbox = draw.textbbox((0, 0), tag_line, font=fonts["xs"])
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, HEIGHT - 100), tag_line, fill=palette["cover_bg"], font=fonts["xs"])

    _accent_bar(draw, palette["cover_bg"], top=False)
    img.save(output_path)
    return output_path


def render_carousel(
    plan: dict[str, Any],
    output_dir: Path | None = None,
    palette: dict | None = None,
) -> list[Path]:
    """
    Render all carousel slides to 1080×1080 PNGs.
    palette: pass a colour scheme dict from color_schemes.py, or None to use the
             current week's palette automatically.
    """
    import tempfile
    from datetime import date
    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())
    output_dir.mkdir(parents=True, exist_ok=True)

    if palette is None:
        week_num = date.today().isocalendar()[1]
        palette = palette_for_week(week_num)

    fonts = _load_fonts()
    slides_data: list[dict] = plan.get("slides") or []
    n_content = min(len(slides_data), 5)
    total = 1 + n_content + 1

    paths: list[Path] = []

    cover_path = output_dir / "slide_01_cover.png"
    _render_cover(plan, fonts, total, palette, cover_path)
    paths.append(cover_path)

    for i, slide in enumerate(slides_data[:5], start=1):
        p = output_dir / f"slide_{i + 1:02d}_content.png"
        _render_content_slide(slide, i + 1, total, plan, fonts, palette, p)
        paths.append(p)

    cta_path = output_dir / f"slide_{total:02d}_cta.png"
    _render_cta_slide(plan, fonts, total, palette, cta_path)
    paths.append(cta_path)

    return paths
