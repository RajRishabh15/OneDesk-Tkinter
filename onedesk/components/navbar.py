"""
OneDesk Navbar - navbar.py
Top header bar: global live search, quick-add task button,
theme dropdown picker, and user profile chip.
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_button, make_separator, Tooltip
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

        # Button anchor coordinates
        btn_x  = self._anchor.winfo_rootx()
        btn_y  = self._anchor.winfo_rooty()
        btn_h  = self._anchor.winfo_height()

        # Actual screen size
        sw = self._anchor.winfo_screenwidth()
        sh = self._anchor.winfo_screenheight()

        # Popup required size — enforce a sensible minimum width
        pw = max(self.winfo_reqwidth(), 220)
        ph = self.winfo_reqheight()

        # Preferred: directly below the button, left-aligned with it
        x = btn_x
        y = btn_y + btn_h + 4

        # ── Clamp: right edge ─────────────────────────────────────────────
        if x + pw > sw - 4:
            x = sw - pw - 4

        # ── Clamp: left edge ──────────────────────────────────────────────
        x = max(4, x)

        # ── Clamp: bottom edge (flip above button if not enough room) ─────
        taskbar_h = 48          # conservative estimate for Windows taskbar
        if y + ph > sh - taskbar_h:
            y = btn_y - ph - 4  # flip upward

        # ── Clamp: top edge ───────────────────────────────────────────────
        y = max(4, y)

        self.geometry(f"{pw}x{ph}+{x}+{y}")



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
#  Account dropdown                                                            #
# --------------------------------------------------------------------------- #

class AccountDropdown(tk.Toplevel):
    """Floating menu anchored below the account icon; provides Settings and Log Out."""

    def __init__(self, anchor_widget, auth, on_settings, on_logout):
        super().__init__(anchor_widget)
        self._auth = auth
        self._on_settings = on_settings
        self._on_logout = on_logout

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=cfg.C("border"))

        self._anchor = anchor_widget

        inner = tk.Frame(self, bg=cfg.C("card"), padx=10, pady=10)
        inner.pack(padx=1, pady=1, fill="both", expand=True)

        # ── User info header ──
        name = self._auth.display_name if self._auth else ""
        email = (self._auth.user.get("email", "") if self._auth and self._auth.user else "")
        if name or email:
            u_frame = tk.Frame(inner, bg=cfg.C("card"))
            u_frame.pack(fill="x", padx=4, pady=(2, 6))
            if name:
                tk.Label(
                    u_frame,
                    text=name,
                    font=cfg.FONT["sm_b"],
                    bg=cfg.C("card"),
                    fg=cfg.C("text"),
                    anchor="w",
                ).pack(fill="x")
            if email:
                tk.Label(
                    u_frame,
                    text=email,
                    font=cfg.FONT["xs"],
                    bg=cfg.C("card"),
                    fg=cfg.C("text3"),
                    anchor="w",
                ).pack(fill="x")

            make_separator(inner, bg=cfg.C("border")).pack(fill="x", padx=2, pady=(4, 6))

        # ── Menu Options ──
        self._make_menu_item(inner, icon="⚙", text="Settings", callback=self._handle_settings)
        self._make_menu_item(inner, icon="🚪", text="Log Out", callback=self._handle_logout, is_danger=True)

        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>",   lambda _: self.destroy())

        self._place()
        self.focus_force()

    def _place(self):
        self._anchor.update_idletasks()
        self.update_idletasks()

        btn_x  = self._anchor.winfo_rootx()
        btn_y  = self._anchor.winfo_rooty()
        btn_w  = self._anchor.winfo_width()
        btn_h  = self._anchor.winfo_height()

        sw = self._anchor.winfo_screenwidth()
        sh = self._anchor.winfo_screenheight()

        pw = max(self.winfo_reqwidth(), 190)
        ph = self.winfo_reqheight()

        # Align right edge of dropdown with right edge of the button
        x = btn_x + btn_w - pw
        y = btn_y + btn_h + 4

        # Clamp right edge
        if x + pw > sw - 8:
            x = sw - pw - 8
        # Clamp left edge
        x = max(8, x)

        # Clamp bottom edge (flip upward if not enough space below)
        taskbar_h = 48
        if y + ph > sh - taskbar_h:
            y = btn_y - ph - 4
        y = max(4, y)

        self.geometry(f"{pw}x{ph}+{x}+{y}")

    def _make_menu_item(self, parent, icon: str, text: str, callback, is_danger: bool = False):
        row = tk.Frame(parent, bg=cfg.C("card"), cursor="hand2", padx=8, pady=6)
        row.pack(fill="x", pady=1)

        fg_col = cfg.C("danger") if is_danger else cfg.C("text")

        icon_lbl = tk.Label(
            row,
            text=icon,
            font=(cfg.FONT_FAMILY, 11),
            bg=cfg.C("card"),
            fg=fg_col,
            cursor="hand2",
            width=2,
            anchor="w",
        )
        icon_lbl.pack(side="left")

        text_lbl = tk.Label(
            row,
            text=text,
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=fg_col,
            cursor="hand2",
            anchor="w",
        )
        text_lbl.pack(side="left", fill="x", expand=True)

        def _on_click():
            try:
                self.destroy()
            except Exception:
                pass
            callback()

        def _on_hover(entering: bool):
            bg = cfg.C("card2") if entering else cfg.C("card")
            row.configure(bg=bg)
            icon_lbl.configure(bg=bg)
            text_lbl.configure(bg=bg)

        for w in (row, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda e: _on_click())
            w.bind("<Enter>",    lambda e: _on_hover(True))
            w.bind("<Leave>",    lambda e: _on_hover(False))

    def _handle_settings(self):
        if self._on_settings:
            self._on_settings()

    def _handle_logout(self):
        if self._on_logout:
            self._on_logout()

    def _on_focus_out(self, event):
        def _check():
            try:
                if self.winfo_exists():
                    focused = self.focus_get()
                    if focused is None or not str(focused).startswith(str(self)):
                        self.destroy()
            except Exception:
                pass
        self.after(150, _check)


# --------------------------------------------------------------------------- #
#  Navbar                                                                      #
# --------------------------------------------------------------------------- #

class Navbar(tk.Frame):
    def __init__(self, parent, store, auth, on_theme_toggle, on_quick_add, on_search, on_settings=None, on_logout=None, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("height", 50)
        super().__init__(parent, **kw)
        self.pack_propagate(False)

        self._store = store
        self._auth  = auth
        self._on_theme_toggle = on_theme_toggle
        self._on_quick_add    = on_quick_add
        self._on_search       = on_search
        self._on_settings     = on_settings
        self._settings_active = False

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

        # Account / user chip (opens Settings)
        self._account_btn = tk.Frame(
            right,
            bg=cfg.C("card"),
            cursor="hand2",
            padx=2,
            pady=2,
            highlightthickness=1,
            highlightbackground=cfg.C("card"),
        )
        self._account_btn.pack(side="left", pady=10)

        self._user_chip = tk.Label(
            self._account_btn,
            text=self._avatar_text(),
            font=cfg.FONT["xs_b"],
            bg=cfg.C("accent"),
            fg="#ffffff",
            padx=9,
            pady=4,
            relief="flat",
            cursor="hand2",
        )
        self._user_chip.pack(side="left")

        from .ui_helpers import Tooltip
        self._tooltip = Tooltip(self._user_chip, "Account & Settings")

        for w in (self._account_btn, self._user_chip):
            w.bind("<Button-1>", lambda e: self._open_settings())
            w.bind("<Enter>",    lambda e: self._on_chip_hover(True), add="+")
            w.bind("<Leave>",    lambda e: self._on_chip_hover(False), add="+")

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

    # ---- Account / Settings -------------------------------------------------
    def _avatar_text(self) -> str:
        name = self._auth.display_name if self._auth else ""
        initials = "".join(p[0].upper() for p in name.split()[:2]) if name else ""
        return initials if initials else "👤"

    def _open_settings(self):
        if hasattr(self, "_tooltip") and self._tooltip:
            self._tooltip._hide(None)
        if self._on_settings:
            self._on_settings()

    def set_settings_active(self, active: bool):
        self._settings_active = active
        if not hasattr(self, "_account_btn") or not self._account_btn.winfo_exists():
            return
        if active:
            self._account_btn.configure(
                highlightbackground=cfg.C("accent"),
                bg=cfg.C("card2"),
            )
            self._user_chip.configure(bg=cfg.C("accent"))
        else:
            self._account_btn.configure(
                highlightbackground=cfg.C("card"),
                bg=cfg.C("card"),
            )
            self._user_chip.configure(bg=cfg.C("accent"))

    def _on_chip_hover(self, entering: bool):
        if self._settings_active:
            return
        if not hasattr(self, "_user_chip") or not self._user_chip.winfo_exists():
            return
        if entering:
            self._user_chip.configure(bg=cfg.C("accent2"))
            self._account_btn.configure(bg=cfg.C("card2"), highlightbackground=cfg.C("border"))
        else:
            self._user_chip.configure(bg=cfg.C("accent"))
            self._account_btn.configure(bg=cfg.C("card"), highlightbackground=cfg.C("card"))

    def refresh_user(self):
        if hasattr(self, "_user_chip") and self._user_chip.winfo_exists():
            self._user_chip.configure(text=self._avatar_text())

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
            if hasattr(self, "_user_chip") and self._user_chip.winfo_exists():
                self._user_chip.configure(
                    bg=cfg.C("accent"),
                    text=self._avatar_text(),
                )
            if hasattr(self, "_account_btn") and self._account_btn.winfo_exists():
                self._account_btn.configure(
                    bg=cfg.C("card2") if self._settings_active else cfg.C("card"),
                    highlightbackground=cfg.C("accent") if self._settings_active else cfg.C("card"),
                )
        except tk.TclError:
            pass
