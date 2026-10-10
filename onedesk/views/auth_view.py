"""
OneDesk Auth View — auth_view.py
Modern, accessible Login and Signup screens with top theme dropdown,
high-contrast typography, interactive segmented mode switcher,
password show/hide toggle, demo account instant sign-in, and full keyboard navigation.
"""

import tkinter as tk
from .. import config as cfg
from ..components.navbar import ThemeDropdown


class AuthView(tk.Frame):
    """
    Manages the Login / Signup flow.
    on_success() is called once a user has successfully authenticated.
    """

    def __init__(self, parent, auth, on_success, on_theme_toggle=None, mode="login", **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._auth            = auth
        self._on_success      = on_success
        self._on_theme_toggle = on_theme_toggle
        self._mode            = mode    # "login" | "signup"
        self._hide_password   = True
        self._theme_popup     = None

        self._build()

    def destroy(self):
        if hasattr(self, "_theme_popup") and self._theme_popup and self._theme_popup.winfo_exists():
            self._theme_popup.destroy()
        super().destroy()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        outer = tk.Frame(self, bg=cfg.C("bg"))
        outer.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Top bar: Theme selector ─────────────────────────────────────────
        top_bar = tk.Frame(outer, bg=cfg.C("bg"))
        top_bar.pack(fill="x", padx=28, pady=18)

        # Left subtle brand badge
        left_badge = tk.Frame(top_bar, bg=cfg.C("bg"))
        left_badge.pack(side="left")
        tk.Label(
            left_badge,
            text="⬡ OneDesk",
            font=cfg.FONT["base_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text2"),
        ).pack(side="left")

        # Right theme picker button with clear border and high contrast
        self._theme_btn = tk.Button(
            top_bar,
            text=cfg.get_theme_icon() + "  Theme  ▾",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            activebackground=cfg.C("card2"),
            activeforeground=cfg.C("text"),
            relief="flat",
            bd=0,
            padx=14,
            pady=6,
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            cursor="hand2",
            command=self._open_theme_picker,
        )
        self._theme_btn.pack(side="right")
        self._theme_btn.bind("<Enter>", lambda _: self._theme_btn.configure(bg=cfg.C("card2"), highlightbackground=cfg.C("accent")))
        self._theme_btn.bind("<Leave>", lambda _: self._theme_btn.configure(bg=cfg.C("card"), highlightbackground=cfg.C("border")))

        # ── Card container ──────────────────────────────────────────────────
        card = tk.Frame(
            outer,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=480)

        # Top accent color bar
        tk.Frame(card, bg=cfg.C("accent"), height=3).pack(fill="x")

        # Inner card body with balanced padding
        body = tk.Frame(card, bg=cfg.C("card"), padx=28, pady=26)
        body.pack(fill="both", expand=True)

        # ── Logo / brand header ─────────────────────────────────────────────
        brand = tk.Frame(body, bg=cfg.C("card"))
        brand.pack(anchor="center", pady=(0, 2))
        tk.Label(
            brand,
            text="⬡",
            font=(cfg.FONT_FAMILY, 24, "bold"),
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
        ).pack(side="left")
        tk.Label(
            brand,
            text=" OneDesk",
            font=cfg.FONT["2xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(side="left")

        tk.Label(
            body,
            text="Your personal productivity workspace.",
            font=cfg.FONT["base"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
        ).pack(pady=(2, 16))

        # ── Segmented Switcher (Sign In / Create Account) ────────────────────
        # Using grid with uniform column weights for 50/50 exact symmetry
        self._tab_bar = tk.Frame(
            body,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=4,
            pady=4,
        )
        self._tab_bar.pack(fill="x", pady=(0, 14))
        self._tab_bar.columnconfigure(0, weight=1, uniform="tab")
        self._tab_bar.columnconfigure(1, weight=1, uniform="tab")

        self._tab_login = tk.Button(
            self._tab_bar,
            text="Sign In",
            font=cfg.FONT["base_b"],
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: self._set_mode("login"),
        )
        self._tab_login.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        self._tab_signup = tk.Button(
            self._tab_bar,
            text="Create Account",
            font=cfg.FONT["base_b"],
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: self._set_mode("signup"),
        )
        self._tab_signup.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

        self._tab_login.bind("<Enter>", lambda _: self._on_tab_hover(self._tab_login, True))
        self._tab_login.bind("<Leave>", lambda _: self._on_tab_hover(self._tab_login, False))
        self._tab_signup.bind("<Enter>", lambda _: self._on_tab_hover(self._tab_signup, True))
        self._tab_signup.bind("<Leave>", lambda _: self._on_tab_hover(self._tab_signup, False))

        # ── Demo Account Tile (2-column grid layout for zero clipping) ──────
        demo_tile = tk.Frame(
            body,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=14,
            pady=10,
        )
        demo_tile.pack(fill="x", pady=(0, 14))
        demo_tile.columnconfigure(0, weight=1)
        demo_tile.columnconfigure(1, weight=0)

        left_demo = tk.Frame(demo_tile, bg=cfg.C("card2"))
        left_demo.grid(row=0, column=0, sticky="w")

        top_demo_row = tk.Frame(left_demo, bg=cfg.C("card2"))
        top_demo_row.pack(anchor="w")
        tk.Label(
            top_demo_row,
            text="⚡",
            font=cfg.FONT["md"],
            bg=cfg.C("card2"),
            fg=cfg.C("warn"),
        ).pack(side="left")
        tk.Label(
            top_demo_row,
            text=" Demo Account",
            font=cfg.FONT["base_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
        ).pack(side="left")

        tk.Label(
            left_demo,
            text="Instant sign-in with sample data",
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(2, 0))

        self._demo_btn = tk.Button(
            demo_tile,
            text="Instant Sign-in →",
            command=self._demo_login,
            font=cfg.FONT["sm_b"],
            bg=cfg.C("accent"),
            fg="#ffffff",
            activebackground=cfg.C("accent2"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
        )
        self._demo_btn.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self._demo_btn.bind("<Enter>", lambda _: self._demo_btn.configure(bg=cfg.C("accent2")))
        self._demo_btn.bind("<Leave>", lambda _: self._demo_btn.configure(bg=cfg.C("accent")))

        # ── Clean Divider ───────────────────────────────────────────────────
        div = tk.Frame(body, bg=cfg.C("card"))
        div.pack(fill="x", pady=(0, 14))
        tk.Frame(div, bg=cfg.C("border"), height=1).pack(side="left", fill="x", expand=True)
        tk.Label(
            div,
            text="  or continue with email  ",
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
        ).pack(side="left")
        tk.Frame(div, bg=cfg.C("border"), height=1).pack(side="left", fill="x", expand=True)

        # ── Error Callout ───────────────────────────────────────────────────
        self._error_frame = tk.Frame(
            body,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("danger"),
            padx=12,
            pady=8,
        )
        self._error_lbl = tk.Label(
            self._error_frame,
            text="",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("danger"),
            wraplength=380,
            justify="left",
        )
        self._error_lbl.pack(side="left")

        # ── Dynamic Form ────────────────────────────────────────────────────
        self._form_frame = tk.Frame(body, bg=cfg.C("card"))
        self._form_frame.pack(fill="x")

        # ── Bottom Toggle Link ──────────────────────────────────────────────
        toggle_frame = tk.Frame(body, bg=cfg.C("card"))
        toggle_frame.pack(pady=(16, 0))
        self._toggle_lbl = tk.Label(
            toggle_frame,
            text="",
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
        )
        self._toggle_lbl.pack(side="left")
        self._toggle_btn = tk.Button(
            toggle_frame,
            text="",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
            activeforeground=cfg.C("accent2"),
            activebackground=cfg.C("card"),
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._switch_mode,
        )
        self._toggle_btn.pack(side="left")
        self._toggle_btn.bind("<Enter>", lambda _: self._toggle_btn.configure(fg=cfg.C("accent2")))
        self._toggle_btn.bind("<Leave>", lambda _: self._toggle_btn.configure(fg=cfg.C("accent")))

        # Render form and tabs initially
        self._render_form()
        self._update_ui_state()

    def _on_tab_hover(self, tab_btn: tk.Button, entering: bool):
        is_active = (tab_btn == self._tab_login and self._mode == "login") or \
                    (tab_btn == self._tab_signup and self._mode == "signup")
        if not is_active:
            tab_btn.configure(bg=cfg.C("card") if entering else cfg.C("card2"))

    def _render_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

        self._name_var  = tk.StringVar()
        self._email_var = tk.StringVar()
        self._pass_var  = tk.StringVar()

        if self._mode == "signup":
            # Full Name field
            self._name_entry = self._make_input_field("Full name", self._name_var)
            self._name_entry.bind("<Return>", lambda _: self._email_entry.focus_set())

        # Email field
        self._email_entry = self._make_input_field("Email address", self._email_var)
        self._email_entry.bind("<Return>", lambda _: self._pass_entry.focus_set())

        # Password field with eye toggle
        self._pass_entry = self._make_password_field("Password", self._pass_var)
        self._pass_entry.bind("<Return>", lambda _: self._submit())

        # Submit button
        btn_text = "Sign In" if self._mode == "login" else "Create Account"
        self._submit_btn = tk.Button(
            self._form_frame,
            text=btn_text,
            command=self._submit,
            font=cfg.FONT["md_b"],
            bg=cfg.C("accent"),
            fg="#ffffff",
            activebackground=cfg.C("accent2"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            pady=10,
            cursor="hand2",
        )
        self._submit_btn.pack(fill="x", pady=(14, 0))
        self._submit_btn.bind("<Enter>", lambda _: self._submit_btn.configure(bg=cfg.C("accent2")))
        self._submit_btn.bind("<Leave>", lambda _: self._submit_btn.configure(bg=cfg.C("accent")))

    def _make_input_field(self, label: str, var: tk.StringVar):
        row = tk.Frame(self._form_frame, bg=cfg.C("card"))
        row.pack(fill="x", pady=(0, 10))

        tk.Label(
            row,
            text=label,
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        outer = tk.Frame(
            row,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        outer.pack(fill="x")

        entry = tk.Entry(
            outer,
            textvariable=var,
            font=cfg.FONT["base"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
        )
        entry.pack(fill="both", expand=True, padx=12, ipady=7)

        entry.bind("<FocusIn>",  lambda _: outer.configure(highlightbackground=cfg.C("accent")))
        entry.bind("<FocusOut>", lambda _: outer.configure(highlightbackground=cfg.C("border")))

        return entry

    def _make_password_field(self, label: str, var: tk.StringVar):
        row = tk.Frame(self._form_frame, bg=cfg.C("card"))
        row.pack(fill="x", pady=(0, 10))

        tk.Label(
            row,
            text=label,
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        outer = tk.Frame(
            row,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        outer.pack(fill="x")

        entry = tk.Entry(
            outer,
            textvariable=var,
            font=cfg.FONT["base"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            show="*" if self._hide_password else "",
        )
        entry.pack(side="left", fill="both", expand=True, padx=(12, 4), ipady=7)

        eye_btn = tk.Button(
            outer,
            text="👁 Show" if self._hide_password else "🔒 Hide",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text2"),
            activebackground=cfg.C("card2"),
            activeforeground=cfg.C("accent"),
            relief="flat",
            bd=0,
            padx=10,
            cursor="hand2",
            command=self._toggle_password_visibility,
        )
        eye_btn.pack(side="right", fill="y")
        self._eye_btn = eye_btn

        entry.bind("<FocusIn>",  lambda _: outer.configure(highlightbackground=cfg.C("accent")))
        entry.bind("<FocusOut>", lambda _: outer.configure(highlightbackground=cfg.C("border")))

        return entry

    def _update_ui_state(self):
        if self._mode == "login":
            self._tab_login.configure(
                bg=cfg.C("accent"),
                fg="#ffffff",
                activebackground=cfg.C("accent"),
                activeforeground="#ffffff",
            )
            self._tab_signup.configure(
                bg=cfg.C("card2"),
                fg=cfg.C("text"),
                activebackground=cfg.C("card"),
                activeforeground=cfg.C("text"),
            )
            self._toggle_lbl.configure(text="Don't have an account? ")
            self._toggle_btn.configure(text="Sign up")
        else:
            self._tab_login.configure(
                bg=cfg.C("card2"),
                fg=cfg.C("text"),
                activebackground=cfg.C("card"),
                activeforeground=cfg.C("text"),
            )
            self._tab_signup.configure(
                bg=cfg.C("accent"),
                fg="#ffffff",
                activebackground=cfg.C("accent"),
                activeforeground="#ffffff",
            )
            self._toggle_lbl.configure(text="Already have an account? ")
            self._toggle_btn.configure(text="Sign in")

    def _toggle_password_visibility(self):
        self._hide_password = not self._hide_password
        show_char = "*" if self._hide_password else ""
        btn_text = "👁 Show" if self._hide_password else "🔒 Hide"
        if hasattr(self, "_pass_entry") and self._pass_entry.winfo_exists():
            self._pass_entry.configure(show=show_char)
        if hasattr(self, "_eye_btn") and self._eye_btn.winfo_exists():
            self._eye_btn.configure(text=btn_text)

    def _set_mode(self, mode: str):
        if self._mode == mode:
            return
        self._mode = mode
        self._hide_error()
        self._render_form()
        self._update_ui_state()

    def _switch_mode(self):
        new_mode = "signup" if self._mode == "login" else "login"
        self._set_mode(new_mode)

    # ── Error Callout ────────────────────────────────────────────────────────
    def _show_error(self, message: str):
        self._error_lbl.configure(text=f"⚠  {message}")
        self._error_frame.pack(fill="x", pady=(0, 12), before=self._form_frame)

    def _hide_error(self):
        self._error_frame.pack_forget()

    # ── Actions ──────────────────────────────────────────────────────────────
    def _submit(self):
        self._hide_error()
        if self._mode == "login":
            email = self._email_var.get().strip()
            pwd = self._pass_var.get().strip()
            if not email or not pwd:
                self._show_error("Please enter both email and password.")
                return
            ok = self._auth.login(email, pwd)
        else:
            name = self._name_var.get().strip()
            email = self._email_var.get().strip()
            pwd = self._pass_var.get().strip()
            if not name or not email or not pwd:
                self._show_error("Please fill in all fields.")
                return
            ok = self._auth.signup(name, email, pwd)

        if ok:
            self._on_success()
        else:
            self._show_error(self._auth.error or "Authentication failed.")

    def _demo_login(self):
        self._auth.demo_login()
        self._on_success()

    def _open_theme_picker(self):
        if self._theme_popup and self._theme_popup.winfo_exists():
            self._theme_popup.destroy()
            self._theme_popup = None
            return
        self._theme_popup = ThemeDropdown(
            anchor_widget=self._theme_btn,
            on_select=self._on_select_theme,
        )

    def _on_select_theme(self, theme_key: str):
        self._theme_popup = None
        if self._on_theme_toggle:
            self._on_theme_toggle(theme_key, mode=self._mode)
