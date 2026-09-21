"""
OneDesk Design System — config.py
Centralised design tokens: palettes, fonts, sizes, and widget styles.
"""

# ── Colour Palettes ──────────────────────────────────────────────────────────

DARK = {
    "bg":          "#0f0c1b",      # root background
    "card":        "#19142b",      # card / panel background
    "card2":       "#201a33",      # slightly lighter card (hover, sidebar items)
    "border":      "#2e2749",      # subtle border
    "accent":      "#a855f7",      # primary accent (purple)
    "accent2":     "#6366f1",      # secondary accent (indigo)
    "accent3":     "#ec4899",      # tertiary accent (pink)
    "text":        "#f0eef8",      # primary text
    "text2":       "#a89fc4",      # secondary / muted text
    "text3":       "#6b5f8a",      # very muted text
    "success":     "#22c55e",      # green
    "warn":        "#f59e0b",      # amber
    "danger":      "#ef4444",      # red
    "sidebar_w":   210,
    "navbar_h":    52,
    "scrollbar_bg":"#1e192f",
    "scrollbar_fg":"#3d3460",
    "entry_bg":    "#141024",
    "entry_sel":   "#2e2749",
    "tag_violet":  ("#c4b5fd", "#2e1a5c"),
    "tag_cyan":    ("#67e8f9", "#0d3a45"),
    "tag_green":   ("#86efac", "#0d3a1e"),
    "tag_amber":   ("#fde68a", "#422006"),
    "tag_rose":    ("#fda4af", "#3b0a18"),
}

LIGHT = {
    "bg":          "#f5f3ff",
    "card":        "#ffffff",
    "card2":       "#ede9fe",
    "border":      "#ddd6fe",
    "accent":      "#7c3aed",
    "accent2":     "#4f46e5",
    "accent3":     "#db2777",
    "text":        "#1e1b4b",
    "text2":       "#4c1d95",
    "text3":       "#7c3aed",
    "success":     "#16a34a",
    "warn":        "#b45309",
    "danger":      "#dc2626",
    "sidebar_w":   210,
    "navbar_h":    52,
    "scrollbar_bg":"#ede9fe",
    "scrollbar_fg":"#c4b5fd",
    "entry_bg":    "#f5f3ff",
    "entry_sel":   "#ddd6fe",
    "tag_violet":  ("#7c3aed", "#ede9fe"),
    "tag_cyan":    ("#0e7490", "#cffafe"),
    "tag_green":   ("#15803d", "#dcfce7"),
    "tag_amber":   ("#b45309", "#fef3c7"),
    "tag_rose":    ("#be123c", "#ffe4e6"),
}

ROSE = {
    "bg":          "#14080e",      # deep velvet wine/rose
    "card":        "#1f0d17",      # burgundy velvet card
    "card2":       "#2b1321",      # interactive hover surface
    "border":      "#3f1931",      # subtle wine border
    "accent":      "#f43f5e",      # primary rose accent
    "accent2":     "#fb7185",      # secondary soft rose coral
    "accent3":     "#fda4af",      # delicate rose petal
    "text":        "#fff1f2",      # crisp rose-tinted white
    "text2":       "#fca5a5",      # soft rose muted text
    "text3":       "#9f1239",      # deep wine muted text
    "success":     "#10b981",      # emerald green
    "warn":        "#f59e0b",      # amber
    "danger":      "#e11d48",      # crimson red
    "sidebar_w":   210,
    "navbar_h":    52,
    "scrollbar_bg":"#1f0d17",
    "scrollbar_fg":"#4c1d3c",
    "entry_bg":    "#180a12",
    "entry_sel":   "#3f1931",
    "tag_violet":  ("#fda4af", "#4c0519"),
    "tag_cyan":    ("#67e8f9", "#083344"),
    "tag_green":   ("#86efac", "#052e16"),
    "tag_amber":   ("#fde68a", "#451a03"),
    "tag_rose":    ("#fb7185", "#3a0916"),
}

AQUA = {
    "bg":          "#051314",      # obsidian oceanic teal
    "card":        "#0b1e20",      # deep lagoon card
    "card2":       "#10292c",      # lighter lagoon surface
    "border":      "#163e41",      # teal border
    "accent":      "#06b6d4",      # electric cyan / aqua
    "accent2":     "#10b981",      # emerald green
    "accent3":     "#14b8a6",      # mint teal
    "text":        "#ecfeff",      # frosted aqua white
    "text2":       "#a5f3fc",      # soft aqua muted text
    "text3":       "#155e75",      # deep teal muted text
    "success":     "#34d399",      # bright mint
    "warn":        "#fbbf24",      # amber
    "danger":      "#f43f5e",      # rose red
    "sidebar_w":   210,
    "navbar_h":    52,
    "scrollbar_bg":"#0b1e20",
    "scrollbar_fg":"#164e52",
    "entry_bg":    "#071719",
    "entry_sel":   "#163e41",
    "tag_violet":  ("#c4b5fd", "#1e1b4b"),
    "tag_cyan":    ("#67e8f9", "#083344"),
    "tag_green":   ("#86efac", "#052e16"),
    "tag_amber":   ("#fde68a", "#451a03"),
    "tag_rose":    ("#fda4af", "#3b0a18"),
}

THEMES = {
    "dark":  DARK,
    "rose":  ROSE,
    "aqua":  AQUA,
    "light": LIGHT,
}

THEME_ORDER = ["dark", "rose", "aqua", "light"]

THEME_META = [
    ("dark",  "Midnight Purple", "🌙", "#a855f7", "#19142b"),
    ("rose",  "Rose Noir",       "🌹", "#f43f5e", "#1f0d17"),
    ("aqua",  "Aqua Emerald",    "🌊", "#06b6d4", "#0b1e20"),
    ("light", "Lavender Light",  "☀",  "#7c3aed", "#ffffff"),
]

# Active palette — mutated at runtime by ThemeManager
_current_theme_key = "dark"
_current = dict(DARK)

def C(key: str) -> str:
    """Look up a colour token from the active palette."""
    return _current[key]

def set_theme(name: str) -> None:
    """Switch the active palette to 'dark', 'rose', 'aqua', or 'light'."""
    global _current_theme_key
    if name not in THEMES:
        name = "dark"
    _current_theme_key = name
    _current.clear()
    _current.update(THEMES[name])

def current_theme_name() -> str:
    return _current_theme_key

def next_theme_name() -> str:
    """Return the next theme in the cycle sequence."""
    idx = THEME_ORDER.index(_current_theme_key) if _current_theme_key in THEME_ORDER else 0
    return THEME_ORDER[(idx + 1) % len(THEME_ORDER)]

def get_theme_icon(name: str = None) -> str:
    k = name or _current_theme_key
    icons = {"dark": "🌙", "rose": "🌹", "aqua": "🌊", "light": "☀"}
    return icons.get(k, "🌙")

# ── Typography ───────────────────────────────────────────────────────────────
FONT_FAMILY  = "Segoe UI"       # primary typeface (Windows)
FONT_MONO    = "Consolas"

FONT = {
    "xs":     (FONT_FAMILY, 8),
    "sm":     (FONT_FAMILY, 9),
    "base":   (FONT_FAMILY, 10),
    "md":     (FONT_FAMILY, 11),
    "lg":     (FONT_FAMILY, 13),
    "xl":     (FONT_FAMILY, 16),
    "2xl":    (FONT_FAMILY, 20),
    "3xl":    (FONT_FAMILY, 26),
    "xs_b":   (FONT_FAMILY, 8,  "bold"),
    "sm_b":   (FONT_FAMILY, 9,  "bold"),
    "base_b": (FONT_FAMILY, 10, "bold"),
    "md_b":   (FONT_FAMILY, 11, "bold"),
    "lg_b":   (FONT_FAMILY, 13, "bold"),
    "xl_b":   (FONT_FAMILY, 16, "bold"),
    "2xl_b":  (FONT_FAMILY, 20, "bold"),
    "mono":   (FONT_MONO, 9),
}

# ── Layout constants ─────────────────────────────────────────────────────────
RADIUS       = 10     # simulated corner radius (for canvas arcs)
PAD          = 12     # standard inner padding
PAD_SM       = 6
CARD_PAD     = 16
WINDOW_W     = 1280
WINDOW_H     = 820
MIN_W        = 1000
MIN_H        = 650

# ── Priority / status colours ────────────────────────────────────────────────
PRIORITY_FG = {"High": "#f87171", "Medium": "#fbbf24", "Low": "#4ade80"}
PRIORITY_BG = {"High": "#3b0a0a", "Medium": "#3b1f00", "Low": "#0a2e1a"}

STATUS_FG  = {"Todo": "#94a3b8", "In Progress": "#818cf8", "Completed": "#4ade80"}
STATUS_BG  = {"Todo": "#1e293b", "In Progress": "#1e1b4b", "Completed": "#0a2e1a"}

COLOR_MAP = {
    "violet": {"dark": ("#c4b5fd", "#2e1a5c"), "light": ("#7c3aed", "#ede9fe")},
    "cyan":   {"dark": ("#67e8f9", "#0d3a45"), "light": ("#0e7490", "#cffafe")},
    "green":  {"dark": ("#86efac", "#0d3a1e"), "light": ("#15803d", "#dcfce7")},
    "amber":  {"dark": ("#fde68a", "#422006"), "light": ("#b45309", "#fef3c7")},
    "rose":   {"dark": ("#fda4af", "#3b0a18"), "light": ("#be123c", "#ffe4e6")},
}

def color_pair(color_name: str) -> tuple:
    """Return (fg, bg) for a note/tag color in the current theme."""
    theme = current_theme_name()
    return COLOR_MAP.get(color_name, COLOR_MAP["violet"])[theme]

# ── Navigation items ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("Dashboard",  "⊞"),
    ("Notes",      "📝"),
    ("Tasks",      "✓"),
    ("Calendar",   "📅"),
    ("Analytics",  "📊"),
    ("Settings",   "⚙"),
]
