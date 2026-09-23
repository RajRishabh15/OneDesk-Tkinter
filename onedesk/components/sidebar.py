"""
OneDesk Sidebar — sidebar.py
Modern collapsible left sidebar with smooth animated width transition,
icon-only collapsed mode, expanded icon+label mode, and a toggle button.
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_separator

# Sidebar width states
EXPANDED_W  = 210
COLLAPSED_W = 58
ANIM_STEPS  = 10
ANIM_MS     = 14


class Sidebar(tk.Frame):
    NAV_ITEMS = [
        ("Dashboard", "⊞"),
        ("Notes",     "📝"),
        ("Tasks",     "✔"),
        ("Calendar",  "📅"),
        ("Analytics", "📊"),
        ("Settings",  "⚙"),
    ]

    def __init__(self, parent, on_navigate, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("width", EXPANDED_W)
        super().__init__(parent, **kw)
        self.pack_propagate(False)

        self._on_navigate = on_navigate
        self._active      = "Dashboard"
        self._btns: dict  = {}   # name -> (outer, inner, icon_lbl, label_lbl, indicator)
        self._expanded    = True
        self._animating   = False
        self._current_w   = EXPANDED_W

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Header: logo + toggle button ──────────────────────────────────
        self._header = tk.Frame(self, bg=cfg.C("card"))
        self._header.pack(fill="x", pady=(12, 0))

        self._logo_icon = tk.Label(
            self._header,
            text="⬡",
            font=(cfg.FONT_FAMILY, 17, "bold"),
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
            cursor="hand2",
        )
        self._logo_icon.pack(side="left", padx=(14, 0))
        self._logo_icon.bind("<Button-1>", lambda e: self.toggle())
        self._logo_icon.bind("<Enter>", lambda e: self._logo_icon.configure(fg=cfg.C("accent2")))
        self._logo_icon.bind("<Leave>", lambda e: self._logo_icon.configure(fg=cfg.C("accent")))

        self._logo_text = tk.Label(
            self._header,
            text="OneDesk",
            font=cfg.FONT["lg_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            cursor="hand2",
        )
        self._logo_text.pack(side="left", padx=(6, 0))
        self._logo_text.bind("<Button-1>", lambda e: self.toggle())
        self._logo_text.bind("<Enter>", lambda e: self._logo_text.configure(fg=cfg.C("accent")))
        self._logo_text.bind("<Leave>", lambda e: self._logo_text.configure(fg=cfg.C("text")))

        # Collapse / expand chevron button (◀ / ▶)
        self._toggle_btn = tk.Button(
            self._header,
            text="◀",
            font=(cfg.FONT_FAMILY, 8),
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
            activebackground=cfg.C("card2"),
            activeforeground=cfg.C("accent"),
            relief="flat",
            bd=0,
            padx=6,
            pady=4,
            cursor="hand2",
            command=self.toggle,
        )
        self._toggle_btn.pack(side="right", padx=(0, 8))

        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=10, pady=(10, 6))

        # ── Section label ─────────────────────────────────────────────────
        self._section_label = tk.Label(
            self,
            text="WORKSPACE",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        )
        self._section_label.pack(anchor="w", padx=18, pady=(0, 4))

        # ── Nav items ─────────────────────────────────────────────────────
        self._nav_frame = tk.Frame(self, bg=cfg.C("card"))
        self._nav_frame.pack(fill="x")

        for name, icon in self.NAV_ITEMS:
            self._make_nav_btn(name, icon)

        # ── Spacer + version ──────────────────────────────────────────────
        tk.Frame(self, bg=cfg.C("card")).pack(fill="both", expand=True)
        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=10, pady=(0, 4))

        self._version_label = tk.Label(
            self,
            text="v1.0",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        )
        self._version_label.pack(anchor="w", padx=18, pady=(0, 12))

    def _make_nav_btn(self, name: str, icon: str):
        outer = tk.Frame(self._nav_frame, bg=cfg.C("card"))
        outer.pack(fill="x", padx=6, pady=1)

        # Active indicator bar
        indicator = tk.Frame(outer, bg=cfg.C("card"), width=3)
        indicator.pack(side="left", fill="y")

        # Clickable inner area
        inner = tk.Frame(outer, bg=cfg.C("card"), cursor="hand2")
        inner.pack(side="left", fill="x", expand=True)

        # Icon
        icon_lbl = tk.Label(
            inner,
            text=icon,
            font=(cfg.FONT_FAMILY, 13),
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
            pady=8,
            cursor="hand2",
        )
        icon_lbl.pack(side="left", padx=(10, 4))

        # Label (hidden in collapsed mode)
        label_lbl = tk.Label(
            inner,
            text=name,
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
            anchor="w",
            cursor="hand2",
        )
        label_lbl.pack(side="left", fill="x", expand=True)

        self._btns[name] = (outer, inner, icon_lbl, label_lbl, indicator)

        # Bind clicks / hover on all sub-widgets
        for w in (outer, inner, icon_lbl, label_lbl):
            w.bind("<Button-1>", lambda e, n=name: self._navigate(n))
            w.bind("<Enter>",    lambda e, n=name: self._on_hover(n, True))
            w.bind("<Leave>",    lambda e, n=name: self._on_hover(n, False))

        self._update_btn_style(name)

    # ── Hover ────────────────────────────────────────────────────────────────
    def _on_hover(self, name: str, entering: bool):
        if name == self._active:
            return
        bg = cfg.C("card2") if entering else cfg.C("card")
        outer, inner, icon_lbl, label_lbl, indicator = self._btns[name]
        for w in (outer, inner, icon_lbl, label_lbl):
            w.configure(bg=bg)

    # ── Navigation ───────────────────────────────────────────────────────────
    def _navigate(self, name: str):
        self._active = name
        for n in self._btns:
            self._update_btn_style(n)
        self._on_navigate(name)

    def _update_btn_style(self, name: str):
        outer, inner, icon_lbl, label_lbl, indicator = self._btns[name]
        if name == self._active:
            bg = cfg.C("card2")
            fg = cfg.C("text")
            indicator.configure(bg=cfg.C("accent"))
        else:
            bg = cfg.C("card")
            fg = cfg.C("text2")
            indicator.configure(bg=cfg.C("card"))
        for w in (outer, inner, icon_lbl, label_lbl):
            w.configure(bg=bg)
        icon_lbl.configure(fg=fg)
        label_lbl.configure(fg=fg)

    def set_active(self, name: str):
        self._active = name
        for n in self._btns:
            self._update_btn_style(n)

    # ── Collapse / Expand animation ───────────────────────────────────────────
    def toggle(self):
        if self._animating:
            return
        self._expanded = not self._expanded
        target = EXPANDED_W if self._expanded else COLLAPSED_W

        # Hide labels immediately when collapsing to avoid overflow flicker
        if not self._expanded:
            self._set_labels_visible(False)

        self._animate_to(target)

    def _animate_to(self, target: int):
        self._animating = True
        start   = self._current_w
        delta   = (target - start) / ANIM_STEPS

        def _step(n):
            if n >= ANIM_STEPS:
                self._current_w = target
                self.configure(width=target)
                self._animating = False
                if self._expanded:
                    self._set_labels_visible(True)
                    self._toggle_btn.configure(text="◀")
                else:
                    self._toggle_btn.configure(text="▶")
                return
            self._current_w = int(start + delta * (n + 1))
            self.configure(width=self._current_w)
            self.after(ANIM_MS, lambda: _step(n + 1))

        _step(0)

    def _set_labels_visible(self, visible: bool):
        """Show/hide text elements that disappear in icon-only mode."""
        if visible:
            self._logo_text.pack(side="left", padx=(6, 0), in_=self._header,
                                 before=self._toggle_btn)
            self._section_label.pack(anchor="w", padx=18, pady=(0, 4))
            for _, (outer, inner, icon_lbl, label_lbl, indicator) in self._btns.items():
                label_lbl.pack(side="left", fill="x", expand=True)
            self._version_label.configure(text="v1.0")
        else:
            self._logo_text.pack_forget()
            self._section_label.pack_forget()
            for _, (outer, inner, icon_lbl, label_lbl, indicator) in self._btns.items():
                label_lbl.pack_forget()
            self._version_label.configure(text="")

    # ── Theme refresh ────────────────────────────────────────────────────────
    def refresh_theme(self):
        self.configure(bg=cfg.C("card"))
        self._header.configure(bg=cfg.C("card"))
        self._logo_icon.configure(bg=cfg.C("card"), fg=cfg.C("accent"))
        self._logo_text.configure(bg=cfg.C("card"), fg=cfg.C("text"))
        self._toggle_btn.configure(
            bg=cfg.C("card"), fg=cfg.C("text3"),
            activebackground=cfg.C("card2"), activeforeground=cfg.C("accent"),
        )
        self._section_label.configure(bg=cfg.C("card"), fg=cfg.C("text3"))
        self._nav_frame.configure(bg=cfg.C("card"))
        self._version_label.configure(bg=cfg.C("card"), fg=cfg.C("text3"))
        for name in self._btns:
            self._update_btn_style(name)
