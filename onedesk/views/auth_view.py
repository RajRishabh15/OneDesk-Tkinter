"""
OneDesk Auth View — auth_view.py
Login and Signup screens with demo instant login.
"""

import tkinter as tk
from .. import config as cfg
from ..components.ui_helpers import make_button, make_entry, make_separator


class AuthView(tk.Frame):
    """
    Manages the Login / Signup flow.
    on_success() is called once a user has successfully authenticated.
    """

    def __init__(self, parent, auth, on_success, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._auth       = auth
        self._on_success = on_success
        self._mode       = "login"    # "login" | "signup"

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Full-screen gradient-ish background
        outer = tk.Frame(self, bg=cfg.C("bg"))
        outer.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Card container
        card = tk.Frame(
            outer,
            bg=cfg.C("card"),
            padx=36,
            pady=36,
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=440)

        # ── Logo / brand ──────────────────────────────────────────────────
        brand = tk.Frame(card, bg=cfg.C("card"))
        brand.pack(anchor="center", pady=(0, 4))
        tk.Label(brand, text="⬡", font=(cfg.FONT_FAMILY, 28, "bold"),
                 bg=cfg.C("card"), fg=cfg.C("accent")).pack(side="left")
        tk.Label(brand, text=" OneDesk", font=cfg.FONT["2xl_b"],
                 bg=cfg.C("card"), fg=cfg.C("text")).pack(side="left")

        tk.Label(card, text="Your personal productivity workspace.",
                 font=cfg.FONT["sm"], bg=cfg.C("card"), fg=cfg.C("text2")).pack(pady=(0, 20))

        make_separator(card, bg=cfg.C("border")).pack(fill="x", pady=(0, 20))

        # ── Demo login tile ───────────────────────────────────────────────
        demo_tile = tk.Frame(card, bg=cfg.C("card2"),
                             highlightthickness=1, highlightbackground=cfg.C("border"))
        demo_tile.pack(fill="x", pady=(0, 16), ipady=8)

        left_demo = tk.Frame(demo_tile, bg=cfg.C("card2"))
        left_demo.pack(side="left", padx=14)
        tk.Label(left_demo, text="⚡", font=cfg.FONT["lg"],
                 bg=cfg.C("card2"), fg=cfg.C("warn")).pack(side="left")
        tk.Label(left_demo, text=" Demo Account", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card2"), fg=cfg.C("text")).pack(side="left")

        make_button(
            demo_tile,
            text="Instant Sign-in →",
            command=self._demo_login,
            variant="primary",
        ).pack(side="right", padx=14, pady=4)

        # ── Divider ───────────────────────────────────────────────────────
        div = tk.Frame(card, bg=cfg.C("card"))
        div.pack(fill="x", pady=(0, 16))
        tk.Frame(div, bg=cfg.C("border"), height=1).pack(fill="x")
        tk.Label(div, text="or with email", font=cfg.FONT["xs"],
                 bg=cfg.C("card"), fg=cfg.C("text3")).pack()

        # ── Dynamic form ──────────────────────────────────────────────────
        self._form_frame = tk.Frame(card, bg=cfg.C("card"))
        self._form_frame.pack(fill="x")

        self._error_lbl = tk.Label(card, text="", font=cfg.FONT["xs"],
                                   bg=cfg.C("card"), fg=cfg.C("danger"))
        self._error_lbl.pack()

        self._render_form()

        # ── Toggle login / signup ─────────────────────────────────────────
        toggle_frame = tk.Frame(card, bg=cfg.C("card"))
        toggle_frame.pack(pady=(12, 0))
        self._toggle_lbl = tk.Label(toggle_frame, text="", font=cfg.FONT["xs"],
                                     bg=cfg.C("card"), fg=cfg.C("text2"))
        self._toggle_lbl.pack(side="left")
        self._toggle_btn = tk.Button(
            toggle_frame,
            text="",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
            activeforeground=cfg.C("accent2"),
            activebackground=cfg.C("card"),
            relief="flat", bd=0, cursor="hand2",
            command=self._switch_mode,
        )
        self._toggle_btn.pack(side="left")
        self._update_toggle()

    def _render_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

        self._name_var  = tk.StringVar()
        self._email_var = tk.StringVar()
        self._pass_var  = tk.StringVar()

        if self._mode == "signup":
            self._make_field("Full name",        self._name_var,  show="")
        self._make_field("Email address",    self._email_var, show="")
        self._make_field("Password",         self._pass_var,  show="*")

        make_button(
            self._form_frame,
            text="Sign In" if self._mode == "login" else "Create Account",
            command=self._submit,
            variant="primary",
        ).pack(fill="x", pady=(14, 0), ipady=4)

    def _make_field(self, label, var, show=""):
        row = tk.Frame(self._form_frame, bg=cfg.C("card"))
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text=label, font=cfg.FONT["xs_b"],
                 bg=cfg.C("card"), fg=cfg.C("text2")).pack(anchor="w")
        e = make_entry(row, textvariable=var, width=34)
        if show:
            e.configure(show=show)
        e.pack(fill="x", ipady=4, pady=(2, 0))
        if label == "Email address":
            e.bind("<Return>", lambda _: self._submit())

    # ── Actions ──────────────────────────────────────────────────────────────
    def _submit(self):
        self._error_lbl.configure(text="")
        if self._mode == "login":
            ok = self._auth.login(self._email_var.get(), self._pass_var.get())
        else:
            ok = self._auth.signup(self._name_var.get(), self._email_var.get(), self._pass_var.get())
        if ok:
            self._on_success()
        else:
            self._error_lbl.configure(text=self._auth.error)

    def _demo_login(self):
        self._auth.demo_login()
        self._on_success()

    def _switch_mode(self):
        self._mode = "signup" if self._mode == "login" else "login"
        self._render_form()
        self._update_toggle()

    def _update_toggle(self):
        if self._mode == "login":
            self._toggle_lbl.configure(text="Don't have an account? ")
            self._toggle_btn.configure(text="Sign up")
        else:
            self._toggle_lbl.configure(text="Already have an account? ")
            self._toggle_btn.configure(text="Sign in")
