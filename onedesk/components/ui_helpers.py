"""
OneDesk UI Helpers — ui_helpers.py
Reusable styled widget factories: buttons, badges, entries, scrollable frames.
"""

import tkinter as tk
from tkinter import ttk
from .. import config as cfg


# ── Styled button ────────────────────────────────────────────────────────────

def make_button(parent, text, command=None, variant="primary", icon="", **kw):
    """
    variant: 'primary' | 'secondary' | 'danger' | 'ghost'
    """
    c = cfg.C

    styles = {
        "primary":   {"bg": c("accent"),  "fg": "#ffffff", "ab": c("accent2")},
        "secondary": {"bg": c("card2"),   "fg": c("text"),  "ab": c("border")},
        "danger":    {"bg": "#7f1d1d",    "fg": "#fca5a5",  "ab": "#b91c1c"},
        "ghost":     {"bg": c("card"),    "fg": c("text2"), "ab": c("card2")},
    }
    s = styles.get(variant, styles["secondary"])
    label = f"{icon} {text}".strip() if icon else text

    btn = tk.Button(
        parent,
        text=label,
        command=command,
        bg=s["bg"],
        fg=s["fg"],
        activebackground=s["ab"],
        activeforeground=s["fg"],
        relief="flat",
        bd=0,
        padx=12,
        pady=5,
        font=cfg.FONT["sm_b"],
        cursor="hand2",
        **kw,
    )
    return btn


# ── Priority / status badge ──────────────────────────────────────────────────

def make_badge(parent, text, kind="priority"):
    """
    kind: 'priority' | 'status' | 'tag'
    """
    if kind == "priority":
        fg = cfg.PRIORITY_FG.get(text, cfg.C("text2"))
        bg = cfg.PRIORITY_BG.get(text, cfg.C("card2"))
    elif kind == "status":
        fg = cfg.STATUS_FG.get(text, cfg.C("text2"))
        bg = cfg.STATUS_BG.get(text, cfg.C("card2"))
    else:
        fg, bg = cfg.color_pair("violet")

    return tk.Label(
        parent,
        text=text,
        font=cfg.FONT["xs_b"],
        bg=bg,
        fg=fg,
        padx=6,
        pady=2,
    )


# ── Section heading ──────────────────────────────────────────────────────────

def make_heading(parent, text, font_key="xl_b", **kw):
    return tk.Label(
        parent,
        text=text,
        font=cfg.FONT[font_key],
        bg=kw.pop("bg", cfg.C("bg")),
        fg=kw.pop("fg", cfg.C("text")),
        **kw,
    )


def make_label(parent, text, font_key="base", muted=False, **kw):
    return tk.Label(
        parent,
        text=text,
        font=cfg.FONT[font_key],
        bg=kw.pop("bg", cfg.C("bg")),
        fg=kw.pop("fg", cfg.C("text2") if muted else cfg.C("text")),
        **kw,
    )


# ── Styled entry ─────────────────────────────────────────────────────────────

def make_entry(parent, textvariable=None, placeholder="", width=30, **kw):
    entry = tk.Entry(
        parent,
        textvariable=textvariable,
        width=width,
        font=cfg.FONT["base"],
        bg=cfg.C("card2"),
        fg=cfg.C("text"),
        insertbackground=cfg.C("text"),
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightcolor=cfg.C("accent"),
        highlightbackground=cfg.C("border"),
        **kw,
    )
    if placeholder and textvariable is None:
        _attach_placeholder(entry, placeholder)
    return entry


def _attach_placeholder(entry: tk.Entry, placeholder: str):
    def on_focus_in(e):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg=cfg.C("text"))

    def on_focus_out(e):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=cfg.C("text3"))

    entry.insert(0, placeholder)
    entry.config(fg=cfg.C("text3"))
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


# ── Styled text area ─────────────────────────────────────────────────────────

def make_text(parent, height=6, width=40, **kw):
    t = tk.Text(
        parent,
        height=height,
        width=width,
        font=cfg.FONT["base"],
        bg=cfg.C("card2"),
        fg=cfg.C("text"),
        insertbackground=cfg.C("text"),
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightcolor=cfg.C("accent"),
        highlightbackground=cfg.C("border"),
        wrap="word",
        padx=8,
        pady=6,
        **kw,
    )
    return t


# ── Separator ────────────────────────────────────────────────────────────────

def make_separator(parent, orient="horizontal", **kw):
    bg = kw.pop("bg", cfg.C("border"))
    if orient == "horizontal":
        return tk.Frame(parent, bg=bg, height=1, **kw)
    else:
        return tk.Frame(parent, bg=bg, width=1, **kw)


# ── Scrollable frame ─────────────────────────────────────────────────────────

class ScrollableFrame(tk.Frame):
    """A Frame with a vertical scrollbar, themed to match the palette."""

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", cfg.C("bg"))
        super().__init__(parent, bg=bg, **kw)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(
            self, orient="vertical",
            command=self._canvas.yview,
            bg=cfg.C("scrollbar_bg"),
            troughcolor=cfg.C("scrollbar_bg"),
            activebackground=cfg.C("scrollbar_fg"),
        )
        self.inner = tk.Frame(self._canvas, bg=bg)

        self._window_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel only when hovering over this specific scroll area
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, _):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _):
        self._canvas.unbind_all("<MouseWheel>")

    def destroy(self):
        try:
            self._canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass
        super().destroy()

    def _on_inner_configure(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self._canvas.itemconfig(self._window_id, width=e.width)

    def _on_mousewheel(self, e):
        try:
            if self._canvas.winfo_exists():
                self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        except tk.TclError:
            pass


# ── Card container ───────────────────────────────────────────────────────────

class Card(tk.Frame):
    """Styled panel card with a coloured left accent bar option."""

    def __init__(self, parent, accent_color=None, **kw):
        bg = kw.pop("bg", cfg.C("card"))
        super().__init__(parent, bg=bg, **kw)
        if accent_color:
            bar = tk.Frame(self, bg=accent_color, width=3)
            bar.pack(side="left", fill="y")

    def pack(self, **kw):
        kw.setdefault("fill", "x")
        kw.setdefault("pady", 3)
        super().pack(**kw)


# ── Pill / chip ──────────────────────────────────────────────────────────────

def make_pill(parent, text, active=False, command=None):
    fg = cfg.C("text") if active else cfg.C("text2")
    bg = cfg.C("accent") if active else cfg.C("card2")
    btn = tk.Button(
        parent,
        text=text,
        font=cfg.FONT["xs_b"],
        fg=fg,
        bg=bg,
        activeforeground=fg,
        activebackground=cfg.C("accent2"),
        relief="flat",
        bd=0,
        padx=10,
        pady=4,
        command=command,
        cursor="hand2",
    )
    return btn


# ── Color dot ────────────────────────────────────────────────────────────────

def make_color_dot(parent, color_name: str, size=12, command=None):
    fg, bg = cfg.color_pair(color_name)
    canvas = tk.Canvas(parent, width=size, height=size, bg=cfg.C("card"), highlightthickness=0)
    canvas.create_oval(1, 1, size - 1, size - 1, fill=fg, outline="")
    if command:
        canvas.bind("<Button-1>", lambda e: command(color_name))
        canvas.config(cursor="hand2")
    return canvas


# ── Theme-aware re-styler ─────────────────────────────────────────────────────

def restyle_widget(widget, **overrides):
    """Apply current theme colours to a widget (for live theme switching)."""
    try:
        widget.configure(**overrides)
    except tk.TclError:
        pass


# ── Tooltip ──────────────────────────────────────────────────────────────────

class Tooltip:
    def __init__(self, widget, text):
        self._widget = widget
        self._text   = text
        self._tip    = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _):
        x, y, _, _ = self._widget.bbox("insert") if hasattr(self._widget, "bbox") else (0, 0, 0, 0)
        x += self._widget.winfo_rootx() + 20
        y += self._widget.winfo_rooty() + 20
        self._tip = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self._text,
            bg=cfg.C("card2"), fg=cfg.C("text"),
            font=cfg.FONT["xs"], relief="flat", padx=6, pady=3,
        ).pack()

    def _hide(self, _):
        if self._tip:
            self._tip.destroy()
            self._tip = None
