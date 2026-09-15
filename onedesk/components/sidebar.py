"""
OneDesk Sidebar — sidebar.py
Left navigation sidebar with branded logo, nav items, and active-pill indicator.
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_separator


class Sidebar(tk.Frame):
    NAV_ICONS = {
        "Dashboard": "⊞",
        "Notes":     "📝",
        "Tasks":     "✔",
        "Calendar":  "📅",
        "Analytics": "📊",
        "Settings":  "⚙",
    }

    def __init__(self, parent, on_navigate, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("width", cfg.C("sidebar_w"))
        super().__init__(parent, **kw)
        self.pack_propagate(False)

        self._on_navigate = on_navigate
        self._active = "Dashboard"
        self._btns: dict[str, tk.Button] = {}

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Logo ──────────────────────────────────────────────────────────
        logo_frame = tk.Frame(self, bg=cfg.C("card"), pady=18)
        logo_frame.pack(fill="x", padx=16)

        tk.Label(
            logo_frame,
            text="⬡",
            font=(cfg.FONT_FAMILY, 20, "bold"),
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
        ).pack(side="left")

        tk.Label(
            logo_frame,
            text=" OneDesk",
            font=cfg.FONT["lg_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(side="left")

        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=12, pady=(0, 8))

        # ── Nav label ─────────────────────────────────────────────────────
        tk.Label(
            self,
            text="WORKSPACE",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(anchor="w", padx=20, pady=(4, 2))

        # ── Nav items ─────────────────────────────────────────────────────
        for name, icon in self.NAV_ICONS.items():
            self._make_nav_btn(name, icon)

        # ── Spacer + version ──────────────────────────────────────────────
        spacer = tk.Frame(self, bg=cfg.C("card"))
        spacer.pack(fill="both", expand=True)

        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=12, pady=(0, 6))

        tk.Label(
            self,
            text="OneDesk  v1.0",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(anchor="w", padx=20, pady=(0, 12))

    def _make_nav_btn(self, name: str, icon: str):
        outer = tk.Frame(self, bg=cfg.C("card"))
        outer.pack(fill="x", padx=8, pady=1)

        # Active indicator bar (left side)
        indicator = tk.Frame(outer, bg=cfg.C("card"), width=3)
        indicator.pack(side="left", fill="y")

        btn = tk.Button(
            outer,
            text=f"  {icon}  {name}",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
            activebackground=cfg.C("card2"),
            activeforeground=cfg.C("text"),
            relief="flat",
            bd=0,
            padx=10,
            pady=9,
            anchor="w",
            cursor="hand2",
            command=lambda n=name, i=indicator: self._navigate(n, i),
        )
        btn.pack(side="left", fill="x", expand=True)

        self._btns[name] = (outer, btn, indicator)
        self._update_btn_style(name)

    # ── Navigation ───────────────────────────────────────────────────────────
    def _navigate(self, name: str, _indicator=None):
        self._active = name
        for n in self._btns:
            self._update_btn_style(n)
        self._on_navigate(name)

    def _update_btn_style(self, name: str):
        outer, btn, indicator = self._btns[name]
        is_active = name == self._active
        if is_active:
            btn.configure(bg=cfg.C("card2"), fg=cfg.C("text"))
            outer.configure(bg=cfg.C("card2"))
            indicator.configure(bg=cfg.C("accent"))
        else:
            btn.configure(bg=cfg.C("card"), fg=cfg.C("text2"))
            outer.configure(bg=cfg.C("card"))
            indicator.configure(bg=cfg.C("card"))

    def set_active(self, name: str):
        self._active = name
        for n in self._btns:
            self._update_btn_style(n)

    def refresh_theme(self):
        self.configure(bg=cfg.C("card"))
        for name, (outer, btn, indicator) in self._btns.items():
            self._update_btn_style(name)
