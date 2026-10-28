"""
OneDesk UI Helpers — ui_helpers.py
Reusable styled widget factories: buttons, badges, entries, scrollable frames.
"""

import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk
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

    font = kw.pop("font", cfg.FONT["sm_b"])
    padx = kw.pop("padx", 12)
    pady = kw.pop("pady", 5)

    btn = tk.Button(
        parent,
        text=label,
        command=command,
        bg=kw.pop("bg", s["bg"]),
        fg=kw.pop("fg", s["fg"]),
        activebackground=kw.pop("activebackground", s["ab"]),
        activeforeground=kw.pop("activeforeground", s["fg"]),
        relief="flat",
        bd=0,
        padx=padx,
        pady=pady,
        font=font,
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


# ── Modern fluid scrollbar ──────────────────────────────────────────────────

class ModernScrollbar(tk.Canvas):
    """
    Ultra-sleek, fluid modern scrollbar widget.
    Features:
    - Custom anti-aliased pill thumb geometry (no vintage arrows or bevels)
    - Hover expansion (6px resting -> 8px active/hovered)
    - Dynamic color shift to accent color on hover and drag
    - Smart auto-hiding when content fits the container viewport
    - Interactive track paging (click above/below jumps a page)
    - Smooth real-time dragging & scrubbing
    - Works with standard Tkinter scrollable widgets via command & set()
    """
    def __init__(
        self,
        parent,
        command=None,
        orient="vertical",
        width=10,
        bg=None,
        thumb_color=None,
        thumb_hover=None,
        auto_hide=True,
        **kw
    ):
        kw.pop("highlightthickness", None)
        kw.pop("bd", None)
        kw.pop("borderwidth", None)
        self._orient = orient
        self._bar_width = width
        self._bg = bg if bg is not None else cfg.C("bg")
        self._thumb_color = thumb_color if thumb_color is not None else cfg.C("scrollbar_fg")
        self._thumb_hover = thumb_hover if thumb_hover is not None else cfg.C("accent")
        self._auto_hide = auto_hide
        self._command = command

        super().__init__(
            parent,
            width=width if orient == "vertical" else None,
            height=width if orient == "horizontal" else None,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
            **kw
        )

        self._first = 0.0
        self._last = 1.0
        self._thumb_start = -1
        self._thumb_end = -1

        self._is_hovered = False
        self._is_dragging = False
        self._drag_start_coord = 0
        self._drag_start_pos = 0.0

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_button_press)
        self.bind("<B1-Motion>", self._on_b1_motion)
        self.bind("<ButtonRelease-1>", self._on_button_release)

    def set(self, first, last):
        try:
            self._first = max(0.0, min(1.0, float(first)))
            self._last = max(0.0, min(1.0, float(last)))
        except (ValueError, TypeError):
            return
        self._redraw()

    def _draw_pill(self, x1, y1, x2, y2, color):
        if x2 <= x1 or y2 <= y1:
            return
        if self._orient == "vertical":
            r = (x2 - x1) / 2.0
            h = y2 - y1
            if h <= 2 * r:
                self.create_oval(x1, y1, x2, y2, fill=color, outline="", tags="thumb")
            else:
                self.create_oval(x1, y1, x2, y1 + 2 * r, fill=color, outline="", tags="thumb")
                self.create_oval(x1, y2 - 2 * r, x2, y2, fill=color, outline="", tags="thumb")
                self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline="", tags="thumb")
        else:
            r = (y2 - y1) / 2.0
            w = x2 - x1
            if w <= 2 * r:
                self.create_oval(x1, y1, x2, y2, fill=color, outline="", tags="thumb")
            else:
                self.create_oval(x1, y1, x1 + 2 * r, y2, fill=color, outline="", tags="thumb")
                self.create_oval(x2 - 2 * r, y1, x2, y2, fill=color, outline="", tags="thumb")
                self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="", tags="thumb")

    def _redraw(self):
        self.delete("all")

        visible_ratio = self._last - self._first
        # Auto-hide when full content is visible
        if self._auto_hide and (visible_ratio >= 0.999 or (self._first <= 0.0 and self._last >= 1.0)):
            self._thumb_start = -1
            self._thumb_end = -1
            return

        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return

        is_active = self._is_hovered or self._is_dragging
        color = self._thumb_hover if is_active else self._thumb_color

        if self._orient == "vertical":
            min_thumb = 24
            pad_y = 2
            available_h = max(1, h - 2 * pad_y)
            thumb_h = max(min_thumb, int(available_h * visible_ratio))
            thumb_h = min(available_h, thumb_h)

            travel_h = available_h - thumb_h
            denom = 1.0 - visible_ratio
            if denom <= 0:
                frac = 0.0
            else:
                frac = min(1.0, max(0.0, self._first / denom))

            y1 = pad_y + int(frac * travel_h)
            y2 = y1 + thumb_h

            self._thumb_start = y1
            self._thumb_end = y2

            pill_w = min(w - 2, 8 if is_active else 6)
            pill_w = max(4, pill_w)
            x1 = max(0, (w - pill_w) // 2)
            x2 = x1 + pill_w

            self._draw_pill(x1, y1, x2, y2, color)
        else:
            min_thumb = 24
            pad_x = 2
            available_w = max(1, w - 2 * pad_x)
            thumb_w = max(min_thumb, int(available_w * visible_ratio))
            thumb_w = min(available_w, thumb_w)

            travel_w = available_w - thumb_w
            denom = 1.0 - visible_ratio
            if denom <= 0:
                frac = 0.0
            else:
                frac = min(1.0, max(0.0, self._first / denom))

            x1 = pad_x + int(frac * travel_w)
            x2 = x1 + thumb_w

            self._thumb_start = x1
            self._thumb_end = x2

            pill_h = min(h - 2, 8 if is_active else 6)
            pill_h = max(4, pill_h)
            y1 = max(0, (h - pill_h) // 2)
            y2 = y1 + pill_h

            self._draw_pill(x1, y1, x2, y2, color)

    def _on_configure(self, _):
        self._redraw()

    def _on_enter(self, _):
        self._is_hovered = True
        self._redraw()

    def _on_leave(self, _):
        self._is_hovered = False
        if not self._is_dragging:
            self._redraw()

    def _on_button_press(self, e):
        coord = e.y if self._orient == "vertical" else e.x
        if self._thumb_start >= 0 and self._thumb_start <= coord <= self._thumb_end:
            self._is_dragging = True
            self._drag_start_coord = coord
            self._drag_start_pos = self._first
        elif self._thumb_start >= 0 and coord < self._thumb_start:
            if self._command:
                self._command("scroll", -1, "pages")
        elif self._thumb_end >= 0 and coord > self._thumb_end:
            if self._command:
                self._command("scroll", 1, "pages")

    def _on_b1_motion(self, e):
        if not self._is_dragging or not self._command:
            return

        coord = e.y if self._orient == "vertical" else e.x
        delta_pixels = coord - self._drag_start_coord

        dim = self.winfo_height() if self._orient == "vertical" else self.winfo_width()
        pad = 2
        available_dim = max(1, dim - 2 * pad)
        visible_ratio = self._last - self._first
        thumb_size = max(24, int(available_dim * visible_ratio))
        travel = available_dim - thumb_size

        if travel <= 0:
            return

        denom = 1.0 - visible_ratio
        if denom <= 0:
            return

        delta_frac = (delta_pixels / float(travel)) * denom
        target_first = max(0.0, min(denom, self._drag_start_pos + delta_frac))
        self._command("moveto", target_first)

    def _on_button_release(self, _):
        self._is_dragging = False
        self._redraw()

    def update_theme(self, bg=None, thumb_color=None, thumb_hover=None):
        if bg is not None:
            self._bg = bg
            self.configure(bg=bg)
        if thumb_color is not None:
            self._thumb_color = thumb_color
        if thumb_hover is not None:
            self._thumb_hover = thumb_hover
        self._redraw()


# ── Scrollable frame ─────────────────────────────────────────────────────────

class ScrollableFrame(tk.Frame):
    """A Frame with a modern ultra-sleek scrollbar, themed to match the palette."""

    def __init__(self, parent, **kw):
        bg = kw.pop("bg", cfg.C("bg"))
        scrollbar_bg = kw.pop("scrollbar_bg", bg)
        thumb_color = kw.pop("thumb_color", cfg.C("scrollbar_fg"))
        thumb_hover = kw.pop("thumb_hover", cfg.C("accent"))
        bar_width = kw.pop("bar_width", 10)
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._scrollbar = ModernScrollbar(
            self,
            orient="vertical",
            command=self._canvas.yview,
            width=bar_width,
            bg=scrollbar_bg,
            thumb_color=thumb_color,
            thumb_hover=thumb_hover,
        )
        self.inner = tk.Frame(self._canvas, bg=bg)

        self._window_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y", padx=(1, 2), pady=2)
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel only when hovering over this specific scroll area
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

    @property
    def canvas(self):
        return self._canvas

    @property
    def scrollbar(self):
        return self._scrollbar

    def scroll_to_top(self):
        self.update_idletasks()
        try:
            self._canvas.yview_moveto(0.0)
        except Exception:
            pass

    def scroll_to_bottom(self):
        self.update_idletasks()
        try:
            self._canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _bind_mousewheel(self, _):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def destroy(self):
        try:
            self._canvas.unbind_all("<MouseWheel>")
            self._canvas.unbind_all("<Button-4>")
            self._canvas.unbind_all("<Button-5>")
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
                if e.delta:
                    self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                elif e.num == 4:
                    self._canvas.yview_scroll(-1, "units")
                elif e.num == 5:
                    self._canvas.yview_scroll(1, "units")
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
        bbox = self._widget.bbox("insert") if hasattr(self._widget, "bbox") else None
        bx, by = (bbox[0], bbox[1]) if bbox else (0, 0)
        x = self._widget.winfo_rootx() + bx + 20
        y = self._widget.winfo_rooty() + by + 20
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


# ── Circular Avatar Generator ────────────────────────────────────────────────

def create_circular_avatar(image_path=None, size=40, text="?", bg=None, fg="#ffffff") -> ImageTk.PhotoImage:
    """
    Creates a smooth circular PhotoImage.
    If image_path is valid, center-crops and masks the image into an anti-aliased circle.
    Otherwise generates a circular badge featuring the user's initials.
    """
    bg_color = bg or cfg.C("accent")
    if image_path and os.path.exists(image_path):
        try:
            im = Image.open(image_path).convert("RGBA")
            w, h = im.size
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            im = im.crop((left, top, left + min_dim, top + min_dim))
            im = im.resize((size, size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            d = ImageDraw.Draw(mask)
            d.ellipse((0, 0, size - 1, size - 1), fill=255)
            im.putalpha(mask)
            return ImageTk.PhotoImage(im)
        except Exception:
            pass

    # Fallback initials avatar
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=bg_color)
    try:
        font_size = max(9, int(size * 0.40))
        font = ImageFont.truetype("segoeui.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    clean_text = text[:2].upper() if text else "?"
    bbox = d.textbbox((0, 0), clean_text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = (size - th) // 2 - bbox[1]
    d.text((tx, ty), clean_text, fill=fg, font=font)
    return ImageTk.PhotoImage(im)


# ── Round Icon Button ────────────────────────────────────────────────────────

class RoundIconButton(tk.Canvas):
    """
    Fluid circular interactive button with hover states.
    Ideal for quick-action icons: complete task (✓), delete task (✕), add (＋).
    """
    def __init__(self, parent, icon="✓", command=None, size=28,
                 bg_color=None, fg_color=None, hover_bg=None, hover_fg=None,
                 border_color=None, font=None, tooltip=None, parent_bg=None, **kw):
        p_bg = parent_bg or (parent.cget("bg") if hasattr(parent, "cget") else cfg.C("card"))
        super().__init__(parent, width=size, height=size, bg=p_bg, highlightthickness=0, **kw)
        self._command = command
        self._size = size
        self._bg_color = bg_color or cfg.C("card2")
        self._fg_color = fg_color or cfg.C("text2")
        self._hover_bg = hover_bg or cfg.C("accent")
        self._hover_fg = hover_fg or "#ffffff"
        self._border_color = border_color or cfg.C("border")
        self._font = font or (cfg.FONT_FAMILY, 9, "bold")
        self._tooltip_text = tooltip

        pad = 2
        self._oval = self.create_oval(
            pad, pad, size - pad, size - pad,
            fill=self._bg_color, outline=self._border_color, width=1
        )
        self._text = self.create_text(
            size // 2, size // 2,
            text=icon, fill=self._fg_color, font=self._font
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.configure(cursor="hand2")

        if tooltip:
            Tooltip(self, tooltip)

    def _on_enter(self, _):
        self.itemconfig(self._oval, fill=self._hover_bg, outline=self._hover_bg)
        self.itemconfig(self._text, fill=self._hover_fg)

    def _on_leave(self, _):
        self.itemconfig(self._oval, fill=self._bg_color, outline=self._border_color)
        self.itemconfig(self._text, fill=self._fg_color)

    def _on_click(self, _):
        if self._command:
            self._command()

    def update_colors(self, bg_color=None, fg_color=None, border_color=None, parent_bg=None):
        if parent_bg:
            self.configure(bg=parent_bg)
        if bg_color:
            self._bg_color = bg_color
            self.itemconfig(self._oval, fill=bg_color)
        if fg_color:
            self._fg_color = fg_color
            self.itemconfig(self._text, fill=fg_color)
        if border_color:
            self._border_color = border_color
            self.itemconfig(self._oval, outline=border_color)


# ── Pill Badge ───────────────────────────────────────────────────────────────

def make_pill_badge(parent, text, bg=None, fg=None, font_key="xs_b", padx=8, pady=3):
    """Creates a rounded pill-shaped badge with clean typography."""
    return tk.Label(
        parent,
        text=text,
        font=cfg.FONT[font_key],
        bg=bg or cfg.C("card2"),
        fg=fg or cfg.C("text2"),
        padx=padx,
        pady=pady,
    )

