"""
OneDesk Navbar — navbar.py
Top header bar: app title, global live search, quick-add task button,
theme toggle, and user profile chip.
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_button


class Navbar(tk.Frame):
    def __init__(self, parent, store, auth, on_theme_toggle, on_quick_add, on_search, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("height", cfg.C("navbar_h"))
        super().__init__(parent, **kw)
        self.pack_propagate(False)

        self._store = store
        self._auth  = auth
        self._on_theme_toggle = on_theme_toggle
        self._on_quick_add    = on_quick_add
        self._on_search       = on_search

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Left: app badge ───────────────────────────────────────────────
        left = tk.Frame(self, bg=cfg.C("card"))
        left.pack(side="left", fill="y", padx=(16, 0))

        tk.Label(
            left,
            text="OneDesk",
            font=cfg.FONT["md_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
        ).pack(side="left", pady=12)

        # ── Center: search bar ────────────────────────────────────────────
        center = tk.Frame(self, bg=cfg.C("card"))
        center.pack(side="left", fill="both", expand=True, padx=24)

        search_outer = tk.Frame(
            center,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        search_outer.pack(pady=10, fill="x")

        tk.Label(
            search_outer,
            text="🔍",
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
        ).pack(side="left", padx=(8, 4))

        self._search_entry = tk.Entry(
            search_outer,
            textvariable=self._search_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
        )
        self._search_entry.pack(side="left", fill="both", expand=True, padx=(0, 8), ipady=3)
        self._search_entry.insert(0, "Search notes, tasks, events…")
        self._search_entry.configure(fg=cfg.C("text3"))
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)

        # ── Right: actions ────────────────────────────────────────────────
        right = tk.Frame(self, bg=cfg.C("card"))
        right.pack(side="right", fill="y", padx=(0, 16))

        # Quick-add button
        make_button(
            right,
            text="+ Task",
            command=self._on_quick_add,
            variant="primary",
        ).pack(side="left", padx=(0, 8), pady=10)

        # Theme toggle
        self._theme_btn = tk.Button(
            right,
            text="🌙" if cfg.current_theme_name() == "dark" else "☀",
            font=cfg.FONT["base"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            activebackground=cfg.C("border"),
            activeforeground=cfg.C("text"),
            relief="flat",
            bd=0,
            padx=8,
            pady=5,
            cursor="hand2",
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="left", padx=(0, 8), pady=10)

        # User profile chip
        name = self._auth.display_name
        initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "?"
        self._user_chip = tk.Label(
            right,
            text=initials,
            font=cfg.FONT["xs_b"],
            bg=cfg.C("accent"),
            fg="#ffffff",
            padx=8,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self._user_chip.pack(side="left", pady=12)

    # ── Callbacks ────────────────────────────────────────────────────────────
    def _search_focus_in(self, _):
        if self._search_entry.get() == "Search notes, tasks, events…":
            self._search_entry.delete(0, "end")
            self._search_entry.configure(fg=cfg.C("text"))

    def _search_focus_out(self, _):
        if not self._search_entry.get():
            self._search_entry.insert(0, "Search notes, tasks, events…")
            self._search_entry.configure(fg=cfg.C("text3"))

    def _on_search_change(self, *_):
        query = self._search_var.get()
        if query and query != "Search notes, tasks, events…":
            self._on_search(query)
        else:
            self._on_search("")

    def _toggle_theme(self):
        self._on_theme_toggle()
        self._theme_btn.configure(
            text="🌙" if cfg.current_theme_name() == "dark" else "☀"
        )

    def refresh_theme(self):
        self.configure(bg=cfg.C("card"))
        self._theme_btn.configure(
            text="🌙" if cfg.current_theme_name() == "dark" else "☀",
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
        )
