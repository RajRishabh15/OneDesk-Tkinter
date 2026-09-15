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
    "sidebar_w":   220,
    "navbar_h":    52,
    "scrollbar_bg":"#1e192f",
    "scrollbar_fg":"#3d3460",
    "entry_bg":    "#13102280",
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
    "sidebar_w":   220,
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

# Active palette — mutated at runtime by ThemeManager
_current = dict(DARK)

def C(key: str) -> str:
    """Look up a colour token from the active palette."""
    return _current[key]

def set_theme(name: str) -> None:
    """Switch the active palette to 'dark' or 'light'."""
    _current.clear()
    _current.update(DARK if name == "dark" else LIGHT)

def current_theme_name() -> str:
    return "dark" if _current["bg"] == DARK["bg"] else "light"

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
WINDOW_H     = 800
MIN_W        = 900
MIN_H        = 600

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
