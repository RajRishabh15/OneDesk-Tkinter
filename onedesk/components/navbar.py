"""
OneDesk Navbar — navbar.py
Top header bar: global live search, quick-add task button,
theme toggle, and user profile chip. Designed to pair with the
collapsible Sidebar (which now carries the app logo).
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_button
from .search_popup import SearchPopup

_PLACEHOLDER = "Search notes, tasks, events…"


class Navbar(tk.Frame):
    def __init__(self, parent, store, auth, on_theme_toggle, on_quick_add, on_search, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("height", 50)
        super().__init__(parent, **kw)
        self.pack_propagate(False)

        self._store = store
        self._auth  = auth
        self._on_theme_toggle = on_theme_toggle
        self._on_quick_add    = on_quick_add
        self._on_search       = on_search

        self._search_popup = None
        self._search_var   = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)

        self._build()
        self._search_popup = SearchPopup(
            self._search_entry, self._store, on_navigate=self._on_search
        )

    def destroy(self):
        if hasattr(self, "_search_popup") and self._search_popup:
            self._search_popup.destroy()
        super().destroy()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Thin accent line at the bottom of the navbar
        self._bottom_line = tk.Frame(self, bg=cfg.C("border"), height=1)
        self._bottom_line.pack(side="bottom", fill="x")

        # ── Center: pill-style search bar ────────────────────────────────
        self._search_outer = tk.Frame(
            self,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        self._search_outer.pack(
            side="left", fill="y", expand=True,
            padx=(16, 0), pady=8, ipadx=2,
        )

        self._search_icon = tk.Label(
            self._search_outer,
            text="🔍",
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
        )
        self._search_icon.pack(side="left", padx=(10, 2))

        self._search_entry = tk.Entry(
            self._search_outer,
            textvariable=self._search_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            width=38,
        )
        self._search_entry.pack(side="left", fill="y", padx=(2, 10), ipady=2)
        self._search_entry.insert(0, _PLACEHOLDER)
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)
        self._search_entry.bind("<Return>",   self._on_search_enter)
        self._search_entry.bind("<Escape>",   lambda _: self._search_popup.hide())

        # ── Right: action cluster ─────────────────────────────────────────
        right = tk.Frame(self, bg=cfg.C("card"))
        right.pack(side="right", fill="y", padx=(0, 14))

        # "+ Task" quick-add button
        make_button(
            right,
            text="＋ Task",
            command=self._on_quick_add,
            variant="primary",
        ).pack(side="left", padx=(0, 8), pady=10)

        # Theme-cycle button — shows an icon for the NEXT theme
        self._theme_btn = tk.Button(
            right,
            text=cfg.get_theme_icon(),
            font=(cfg.FONT_FAMILY, 11),
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            activebackground=cfg.C("border"),
            activeforeground=cfg.C("text"),
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="left", padx=(0, 10), pady=10)

        # Separator line before avatar
        tk.Frame(right, bg=cfg.C("border"), width=1).pack(
            side="left", fill="y", pady=12, padx=(0, 10)
        )

        # User avatar chip
        name = self._auth.display_name
        initials = "".join(p[0].upper() for p in name.split()[:2]) if name else "?"
        self._user_chip = tk.Label(
            right,
            text=initials,
            font=cfg.FONT["xs_b"],
            bg=cfg.C("accent"),
            fg="#ffffff",
            padx=9,
            pady=5,
            relief="flat",
            cursor="hand2",
        )
        self._user_chip.pack(side="left", pady=12)

    # ── Search callbacks ─────────────────────────────────────────────────────
    def _search_focus_in(self, _):
        if self._search_entry.get() == _PLACEHOLDER:
            self._search_entry.delete(0, "end")
            self._search_entry.configure(fg=cfg.C("text"))
        # Highlight border on focus
        self._search_outer.configure(highlightbackground=cfg.C("accent"))

    def _search_focus_out(self, _):
        if not self._search_entry.get():
            self._search_entry.insert(0, _PLACEHOLDER)
            self._search_entry.configure(fg=cfg.C("text3"))
        self._search_outer.configure(highlightbackground=cfg.C("border"))

    def _on_search_change(self, *_):
        if getattr(self, "_search_popup", None) is None:
            return
        query = self._search_var.get().strip()
        if query and query != _PLACEHOLDER:
            self._search_popup.show(query)
        else:
            self._search_popup.hide()

    def _on_search_enter(self, _):
        if getattr(self, "_search_popup", None) is None:
            return
        query = self._search_var.get().strip()
        if query and query != _PLACEHOLDER:
            self._search_popup.hide()
            if self._on_search:
                self._on_search(query)

    # ── Theme toggle ─────────────────────────────────────────────────────────
    def _toggle_theme(self):
        self._on_theme_toggle()
        try:
            if hasattr(self, "_theme_btn") and self._theme_btn.winfo_exists():
                self._theme_btn.configure(text=cfg.get_theme_icon())
        except tk.TclError:
            pass

    def refresh_theme(self):
        try:
            self.configure(bg=cfg.C("card"))
            self._bottom_line.configure(bg=cfg.C("border"))
            self._search_outer.configure(
                bg=cfg.C("card2"),
                highlightbackground=cfg.C("border"),
            )
            self._search_icon.configure(bg=cfg.C("card2"), fg=cfg.C("text3"))
            self._search_entry.configure(
                bg=cfg.C("card2"), fg=cfg.C("text3"),
                insertbackground=cfg.C("text"),
            )
            if hasattr(self, "_theme_btn") and self._theme_btn.winfo_exists():
                self._theme_btn.configure(
                    text=cfg.get_theme_icon(),
                    bg=cfg.C("card2"),
                    fg=cfg.C("text"),
                    activebackground=cfg.C("border"),
                )
            self._user_chip.configure(bg=cfg.C("accent"))
        except tk.TclError:
            pass
