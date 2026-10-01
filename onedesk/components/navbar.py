"""
OneDesk Navbar - navbar.py
Top header bar: global live search, quick-add task button,
theme dropdown picker, and user profile chip.
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_button
from .search_popup import SearchPopup

_PLACEHOLDER = "Search notes, tasks, events…"


# --------------------------------------------------------------------------- #
#  Theme dropdown                                                              #
# --------------------------------------------------------------------------- #

class ThemeDropdown(tk.Toplevel):
    """Floating panel anchored below the theme button; lists all 4 themes."""

    def __init__(self, anchor_widget, on_select):
        super().__init__(anchor_widget)
        self._on_select = on_select

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=cfg.C("border"))

        self._anchor = anchor_widget

        # Build content FIRST so winfo_reqwidth/height are accurate in _place()
        inner = tk.Frame(self, bg=cfg.C("card"), padx=10, pady=10)
        inner.pack(padx=1, pady=1, fill="both", expand=True)

        tk.Label(
            inner,
            text="Choose theme",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(anchor="w", pady=(0, 8))

        for key, name, icon, accent, bg_col in cfg.THEME_META:
            self._make_row(inner, key, name, icon, accent)

        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>",   lambda _: self.destroy())

        # Place AFTER layout so size is known
        self._place()
        self.focus_force()


    def _place(self):
        self._anchor.update_idletasks()
        self.update_idletasks()

        # Anchor position
        btn_x = self._anchor.winfo_rootx()
        btn_y = self._anchor.winfo_rooty() + self._anchor.winfo_height() + 4

        # Screen dimensions
        sw = self._anchor.winfo_screenwidth()
        sh = self._anchor.winfo_screenheight()

        # Popup dimensions (after layout)
        pw = self.winfo_reqwidth()
        ph = self.winfo_reqheight()

        # Clamp so it never goes off the right or bottom edge
        x = min(btn_x, sw - pw - 4)
        y = btn_y
        if y + ph > sh - 40:          # too close to bottom — flip upward
            y = self._anchor.winfo_rooty() - ph - 4

        self.geometry(f"+{max(0, x)}+{max(0, y)}")


    def _make_row(self, parent, key, name, icon, accent):
        is_active = cfg.current_theme_name() == key
        row_bg = cfg.C("card2") if is_active else cfg.C("card")
        row_fg = cfg.C("text")  if is_active else cfg.C("text2")

        row = tk.Frame(parent, bg=row_bg, cursor="hand2", padx=8, pady=6)
        row.pack(fill="x", pady=1)

        # Colour swatch square
        swatch = tk.Frame(row, bg=accent, width=18, height=18)
        swatch.pack(side="left")
        swatch.pack_propagate(False)

        if is_active:
            tk.Label(swatch, text="✓", font=(cfg.FONT_FAMILY, 7, "bold"),
                     bg=accent, fg="#fff").pack(expand=True)

        lbl = tk.Label(row, text=f"  {icon}  {name}",
                       font=cfg.FONT["sm_b"], bg=row_bg, fg=row_fg, cursor="hand2")
        lbl.pack(side="left")

        def _click(k=key):
            self._on_select(k)
            self.destroy()

        for w in (row, swatch, lbl):
            try:
                w.bind("<Button-1>", lambda e, fn=_click: fn())
                w.bind("<Enter>",    lambda e, r=row: r.configure(bg=cfg.C("card2")))
                w.bind("<Leave>",    lambda e, r=row, rb=row_bg: r.configure(bg=rb))
            except Exception:
                pass

    def _on_focus_out(self, event):
        try:
            if self.focus_get() is None:
                self.destroy()
        except Exception:
            self.destroy()


# --------------------------------------------------------------------------- #
#  Navbar                                                                      #
# --------------------------------------------------------------------------- #

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
        self._theme_popup  = None
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

    # ---- Build --------------------------------------------------------------
    def _build(self):
        # Thin separator at the very bottom
        self._bottom_line = tk.Frame(self, bg=cfg.C("border"), height=1)
        self._bottom_line.pack(side="bottom", fill="x")

        # Search bar (left-expanding)
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

        # Right cluster
        right = tk.Frame(self, bg=cfg.C("card"))
        right.pack(side="right", fill="y", padx=(0, 14))

        # Quick-add task
        make_button(
            right,
            text="＋ Task",
            command=self._on_quick_add,
            variant="primary",
        ).pack(side="left", padx=(0, 8), pady=10)

        # Theme dropdown button
        self._theme_btn = tk.Button(
            right,
            text=self._theme_label(),
            font=(cfg.FONT_FAMILY, 10),
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            activebackground=cfg.C("border"),
            activeforeground=cfg.C("text"),
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._open_theme_picker,
        )
        self._theme_btn.pack(side="left", padx=(0, 10), pady=10)

        # Vertical separator
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

    # ---- Theme picker -------------------------------------------------------
    def _theme_label(self) -> str:
        return cfg.get_theme_icon() + "  Theme  ▾"

    def _open_theme_picker(self):
        if self._theme_popup and self._theme_popup.winfo_exists():
            self._theme_popup.destroy()
            self._theme_popup = None
            return
        self._theme_popup = ThemeDropdown(
            anchor_widget=self._theme_btn,
            on_select=self._select_theme,
        )

    def _select_theme(self, theme_key: str):
        self._theme_popup = None
        self._on_theme_toggle(theme_key)
        try:
            if hasattr(self, "_theme_btn") and self._theme_btn.winfo_exists():
                self._theme_btn.configure(text=self._theme_label())
        except tk.TclError:
            pass

    # ---- Search callbacks ---------------------------------------------------
    def _search_focus_in(self, _):
        if self._search_entry.get() == _PLACEHOLDER:
            self._search_entry.delete(0, "end")
            self._search_entry.configure(fg=cfg.C("text"))
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

    # ---- Theme refresh ------------------------------------------------------
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
                    text=self._theme_label(),
                    bg=cfg.C("card2"),
                    fg=cfg.C("text"),
                    activebackground=cfg.C("border"),
                )
            self._user_chip.configure(bg=cfg.C("accent"))
        except tk.TclError:
            pass
