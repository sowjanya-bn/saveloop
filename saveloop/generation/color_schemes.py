from __future__ import annotations

# Eight palettes that move gradually across the warm→cool→warm colour spectrum.
# Each week advances one step. After 8 weeks the cycle restarts with a fresh eye.
#
# Each palette has:
#   bg          — slide background (light)
#   cover_bg    — cover/CTA slide background (dark)
#   accent      — highlight bar, rules, CTA slide background accent
#   text        — primary text
#   subtext     — body text
#   muted       — counters, watermarks, hints
#   cover_text  — text on dark cover slide
#   name        — human label shown in the UI

PALETTES: list[dict] = [
    {   # 0 — Warm Cream  (starting point, your current default)
        "name":       "Warm Cream",
        "bg":         (247, 244, 238),
        "cover_bg":   (30,  30,  30),
        "accent":     (212, 165, 116),
        "text":       (26,  26,  26),
        "subtext":    (90,  85,  78),
        "muted":      (150, 144, 136),
        "cover_text": (247, 244, 238),
    },
    {   # 1 — Warm Sand  (golden shift)
        "name":       "Warm Sand",
        "bg":         (250, 246, 232),
        "cover_bg":   (70,  55,  30),
        "accent":     (195, 160,  85),
        "text":       (50,  38,  20),
        "subtext":    (100,  85,  55),
        "muted":      (160, 148, 120),
        "cover_text": (250, 246, 232),
    },
    {   # 2 — Terracotta  (warm orange-red)
        "name":       "Terracotta",
        "bg":         (250, 242, 236),
        "cover_bg":   (95,  50,  35),
        "accent":     (200, 110,  75),
        "text":       (55,  30,  20),
        "subtext":    (110,  75,  60),
        "muted":      (165, 138, 128),
        "cover_text": (250, 242, 236),
    },
    {   # 3 — Dusty Rose  (warm pink)
        "name":       "Dusty Rose",
        "bg":         (250, 242, 244),
        "cover_bg":   (80,  42,  50),
        "accent":     (195, 130, 140),
        "text":       (50,  25,  30),
        "subtext":    (110,  75,  82),
        "muted":      (165, 138, 142),
        "cover_text": (250, 242, 244),
    },
    {   # 4 — Lavender  (crossing into cool)
        "name":       "Lavender",
        "bg":         (244, 241, 252),
        "cover_bg":   (52,  38,  80),
        "accent":     (158, 130, 210),
        "text":       (35,  25,  55),
        "subtext":    (90,  78, 118),
        "muted":      (148, 140, 168),
        "cover_text": (244, 241, 252),
    },
    {   # 5 — Slate Blue  (cool blue)
        "name":       "Slate Blue",
        "bg":         (238, 242, 250),
        "cover_bg":   (30,  38,  68),
        "accent":     (108, 132, 200),
        "text":       (22,  28,  55),
        "subtext":    (72,  85, 125),
        "muted":      (138, 148, 180),
        "cover_text": (238, 242, 250),
    },
    {   # 6 — Mint  (cool green-teal)
        "name":       "Mint",
        "bg":         (236, 248, 244),
        "cover_bg":   (25,  58,  50),
        "accent":     (85,  172, 148),
        "text":       (18,  48,  40),
        "subtext":    (62,  105,  90),
        "muted":      (128, 165, 152),
        "cover_text": (236, 248, 244),
    },
    {   # 7 — Sage  (muted green, bridging back to warm)
        "name":       "Sage",
        "bg":         (240, 245, 238),
        "cover_bg":   (38,  55,  38),
        "accent":     (130, 168, 118),
        "text":       (28,  42,  25),
        "subtext":    (75,  102,  68),
        "muted":      (138, 160, 132),
        "cover_text": (240, 245, 238),
    },
]


def palette_for_week(week_number: int) -> dict:
    """Return the palette for a given ISO week number (cycles every 8 weeks)."""
    return PALETTES[week_number % len(PALETTES)]


def palette_index_for_week(week_number: int) -> int:
    return week_number % len(PALETTES)
