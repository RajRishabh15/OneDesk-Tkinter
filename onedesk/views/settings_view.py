"""
OneDesk Settings View — settings_view.py
Profile management, theme toggle, JSON backup export/import, data reset, sign out.
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from .. import config as cfg
from ..components.ui_helpers import make_button, make_separator, make_entry
from ..components.modals import confirm


class SettingsView(tk.Frame):
    def __init__(self, parent, store, auth, on_theme_toggle, on_logout, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store           = store
        self._auth            = auth
        self._on_theme_toggle = on_theme_toggle
        self._on_logout       = on_logout

        self._build()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Scrollable area
        from ..components.ui_helpers import ScrollableFrame
        scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        scroll.pack(fill="both", expand=True)
        inner = scroll.inner

        pad = cfg.PAD

        # ── Page heading ──────────────────────────────────────────────────
        hdr = tk.Frame(inner, bg=cfg.C("bg"))
        hdr.pack(fill="x", padx=pad, pady=(pad, 4))
        tk.Label(hdr, text="Settings", font=cfg.FONT["2xl_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text")).pack(anchor="w")
        tk.Label(hdr, text="Manage your profile, appearance, and data.",
                 font=cfg.FONT["sm"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w", pady=(2, 0))

        make_separator(inner, bg=cfg.C("border")).pack(fill="x", padx=pad, pady=8)

        # ── Profile section ───────────────────────────────────────────────
        self._section(inner, "👤  Profile")
        profile_card = self._card(inner)

        name_row = tk.Frame(profile_card, bg=cfg.C("card"))
        name_row.pack(fill="x", pady=(0, 8))
        tk.Label(name_row, text="Display Name", font=cfg.FONT["xs_b"],
                 bg=cfg.C("card"), fg=cfg.C("text2"), width=16, anchor="w").pack(side="left")
        self._name_var = tk.StringVar(value=self._auth.display_name)
        make_entry(profile_card, textvariable=self._name_var, width=30).pack(anchor="w", pady=(0, 4))

        email_lbl = self._auth.user.get("email", "") if self._auth.user else ""
        tk.Label(profile_card, text=f"Email: {email_lbl}", font=cfg.FONT["xs"],
                 bg=cfg.C("card"), fg=cfg.C("text3")).pack(anchor="w", pady=(0, 8))

        self._save_feedback = tk.Label(profile_card, text="", font=cfg.FONT["xs"],
                                        bg=cfg.C("card"), fg=cfg.C("success"))
        self._save_feedback.pack(anchor="w", pady=(0, 4))

        make_button(profile_card, "Save Profile", command=self._save_profile, variant="primary").pack(anchor="w")

        # ── Appearance ────────────────────────────────────────────────────
        self._section(inner, "🎨  Appearance")
        app_card = self._card(inner)

        self._theme_var = tk.StringVar(value=cfg.current_theme_name())
        theme_grid = tk.Frame(app_card, bg=cfg.C("card"))
        theme_grid.pack(fill="x", pady=(4, 0))

        for i, (t_key, t_label, t_icon, t_accent, t_bg) in enumerate(cfg.THEME_META):
            is_active = (t_key == cfg.current_theme_name())
            t_card = tk.Frame(
                theme_grid,
                bg=cfg.C("card2") if not is_active else cfg.C("border"),
                highlightthickness=2 if is_active else 1,
                highlightbackground=cfg.C("accent") if is_active else cfg.C("border"),
                padx=14,
                pady=12,
                cursor="hand2",
            )
            t_card.grid(row=0, column=i, padx=4, sticky="nsew")
            theme_grid.columnconfigure(i, weight=1)

            # Swatch & Radio row
            top_t = tk.Frame(t_card, bg=t_card["bg"])
            top_t.pack(fill="x")
            tk.Label(top_t, text=t_icon, font=cfg.FONT["lg"], bg=t_card["bg"]).pack(side="left")

            # Swatch preview dots
            swatch = tk.Frame(top_t, bg=t_card["bg"])
            swatch.pack(side="right")
            tk.Label(swatch, text="●", font=cfg.FONT["xs"], fg=t_accent, bg=t_card["bg"]).pack(side="left")
            tk.Label(swatch, text="●", font=cfg.FONT["xs"], fg=t_bg, bg=t_card["bg"]).pack(side="left")

            # Label
            lbl = tk.Label(
                t_card,
                text=t_label,
                font=cfg.FONT["sm_b" if is_active else "sm"],
                bg=t_card["bg"],
                fg=cfg.C("accent") if is_active else cfg.C("text"),
                anchor="w",
            )
            lbl.pack(fill="x", pady=(6, 2))

            tag_txt = "Active" if is_active else "Click to apply"
            tag_lbl = tk.Label(
                t_card,
                text=tag_txt,
                font=cfg.FONT["xs"],
                bg=t_card["bg"],
                fg=cfg.C("success") if is_active else cfg.C("text3"),
                anchor="w",
            )
            tag_lbl.pack(anchor="w")

            # Click binding
            def _choose(k=t_key):
                self._theme_var.set(k)
                self._apply_theme(k)

            for w in (t_card, top_t, lbl, tag_lbl, swatch):
                w.bind("<Button-1>", lambda _, k=t_key: _choose(k))

        # ── Data management ───────────────────────────────────────────────
        self._section(inner, "💾  Data Management")
        data_card = self._card(inner)

        actions = [
            ("Export Backup (JSON)", self._export_backup,  "secondary"),
            ("Import Backup (JSON)", self._import_backup,  "ghost"),
            ("Clear All Data",       self._clear_data,     "danger"),
        ]
        for label, cmd, variant in actions:
            btn_row = tk.Frame(data_card, bg=cfg.C("card"))
            btn_row.pack(fill="x", pady=3)
            make_button(btn_row, label, command=cmd, variant=variant).pack(side="left")

            desc = {
                "Export Backup (JSON)": "Save all notes, tasks, and events to a JSON file.",
                "Import Backup (JSON)": "Restore data from a previously exported JSON backup.",
                "Clear All Data":       "⚠ Permanently delete all notes, tasks, and events.",
            }.get(label, "")
            tk.Label(btn_row, text=desc, font=cfg.FONT["xs"],
                     bg=cfg.C("card"), fg=cfg.C("text3")).pack(side="left", padx=12)

        # ── Account ───────────────────────────────────────────────────────
        self._section(inner, "🔐  Account")
        acct_card = self._card(inner)

        make_button(
            acct_card, "Sign Out", command=self._logout, variant="danger",
        ).pack(anchor="w")

        tk.Label(acct_card, text="You will be returned to the login screen.",
                 font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("text3")).pack(anchor="w", pady=(4, 0))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _section(self, parent, title: str):
        frame = tk.Frame(parent, bg=cfg.C("bg"))
        frame.pack(fill="x", padx=cfg.PAD, pady=(12, 4))
        tk.Label(frame, text=title, font=cfg.FONT["md_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text")).pack(anchor="w")

    def _card(self, parent) -> tk.Frame:
        card = tk.Frame(parent, bg=cfg.C("card"),
                         highlightthickness=1, highlightbackground=cfg.C("border"),
                         padx=20, pady=16)
        card.pack(fill="x", padx=cfg.PAD, pady=4)
        return card

    # ── Actions ──────────────────────────────────────────────────────────────
    def _save_profile(self):
        new_name = self._name_var.get().strip()
        if new_name:
            self._auth.update_profile(name=new_name)
            self._save_feedback.configure(text="✓ Profile saved!")
            self.after(1800, lambda: self._save_feedback.configure(text=""))

    def _apply_theme(self, theme_key=None):
        selected = theme_key or self._theme_var.get()
        current  = cfg.current_theme_name()
        if selected != current:
            self._on_theme_toggle(selected)

    def _export_backup(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="onedesk-backup.json",
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        backup = self._store.get_backup()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Exported", f"Backup saved to:\n{path}")

    def _import_backup(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                backup = json.load(f)
            self._store.restore_backup(backup)
            messagebox.showinfo("Imported", "Backup restored successfully!")
        except Exception as e:
            messagebox.showerror("Import Failed", f"Could not read the backup file:\n{e}")

    def _clear_data(self):
        confirm(
            self,
            "This will permanently delete all notes, tasks, and events. This cannot be undone. Continue?",
            self._store.clear_all,
        )

    def _logout(self):
        self._auth.logout()
        self._on_logout()
