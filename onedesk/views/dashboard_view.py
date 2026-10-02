"""
OneDesk Dashboard View - dashboard_view.py
Clean at-a-glance overview: greeting, stat strip, 3-column lower panel.
"""

import tkinter as tk
import time
from datetime import date
from .. import config as cfg
from ..components.ui_helpers import make_button, make_separator, ScrollableFrame
from ..components.modals import TaskDialog


class DashboardView(tk.Frame):
    def __init__(self, parent, store, auth, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store = store
        self._auth  = auth
        self._store.subscribe(self._refresh)
        self._build()

    def destroy(self):
        self._store.unsubscribe(self._refresh)
        super().destroy()

    def _build(self):
        self._scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        self._scroll.pack(fill="both", expand=True)
        self._container = self._scroll.inner
        self._render()

    def _refresh(self):
        for w in self._container.winfo_children():
            w.destroy()
        self._render()

    @staticmethod
    def _greeting():
        h = time.localtime().tm_hour
        if h < 12:  return "Good morning"
        if h < 17:  return "Good afternoon"
        return "Good evening"

    def _card(self, parent, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", cfg.C("border"))
        return tk.Frame(parent, **kw)

    def _render(self):
        P     = 16
        store = self._store
        today = date.today()

        # ── 1. Compact greeting banner ────────────────────────────────────
        banner = tk.Frame(self._container, bg=cfg.C("bg"))
        banner.pack(fill="x", padx=P, pady=(P, 8))

        left_b = tk.Frame(banner, bg=cfg.C("bg"))
        left_b.pack(side="left", fill="y")

        name = self._auth.display_name or "there"
        tk.Label(
            left_b,
            text=f"{self._greeting()}, {name} \U0001f44b",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("bg"), fg=cfg.C("text"), anchor="w",
        ).pack(anchor="w")
        tk.Label(
            left_b,
            text=today.strftime("%A, %B %d  \u2022  Here\'s your overview"),
            font=cfg.FONT["xs"],
            bg=cfg.C("bg"), fg=cfg.C("text3"), anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Quick-add on the right
        right_b = tk.Frame(banner, bg=cfg.C("bg"))
        right_b.pack(side="right", anchor="s")

        self._inline_var = tk.StringVar()
        _PH = "Quick-add a task\u2026"

        qa_wrap = tk.Frame(
            right_b,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        qa_wrap.pack(side="left", padx=(0, 8))

        qa_entry = tk.Entry(
            qa_wrap,
            textvariable=self._inline_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
            insertbackground=cfg.C("text"),
            relief="flat", bd=0, width=26,
        )
        qa_entry.pack(padx=10, pady=6)
        qa_entry.insert(0, _PH)

        def _fi(e):
            if qa_entry.get() == _PH:
                qa_entry.delete(0, "end")
                qa_entry.configure(fg=cfg.C("text"))
            qa_wrap.configure(highlightbackground=cfg.C("accent"))

        def _fo(e):
            if not qa_entry.get():
                qa_entry.insert(0, _PH)
                qa_entry.configure(fg=cfg.C("text3"))
            qa_wrap.configure(highlightbackground=cfg.C("border"))

        qa_entry.bind("<FocusIn>",  _fi)
        qa_entry.bind("<FocusOut>", _fo)
        qa_entry.bind("<Return>",   self._quick_add)

        make_button(right_b, text="Add", command=self._quick_add,
                    variant="primary").pack(side="left", padx=(0, 6))
        make_button(right_b, text="+ Full",
                    command=lambda: TaskDialog(self, self._on_add_task),
                    variant="secondary").pack(side="left")

        # ── 2. Stat strip ─────────────────────────────────────────────────
        total     = len(store.tasks)
        completed = len(store.completed_tasks)
        pending   = len(store.pending_tasks)
        pct       = store.completion_pct

        strip = tk.Frame(self._container, bg=cfg.C("bg"))
        strip.pack(fill="x", padx=P, pady=(0, 10))

        stat_defs = [
            ("\U0001f4cb", "Tasks",   str(total),                cfg.C("accent")),
            ("\u2705",     "Done",    str(completed),            cfg.C("success")),
            ("\u23f3",     "Pending", str(pending),              cfg.C("warn")),
            ("\U0001f4dd", "Notes",   str(len(store.notes)),     cfg.C("accent2")),
            ("\U0001f4c5", "Today",   str(len(store.today_events)), cfg.C("accent3")),
        ]

        for i, (icon, label, value, color) in enumerate(stat_defs):
            sc = self._card(strip, padx=14, pady=10)
            sc.grid(row=0, column=i, padx=(0, 6), sticky="nsew")
            strip.columnconfigure(i, weight=1)

            hdr = tk.Frame(sc, bg=cfg.C("card"))
            hdr.pack(fill="x")
            tk.Label(hdr, text=icon, font=cfg.FONT["base"],
                     bg=cfg.C("card"), fg=color).pack(side="left")
            tk.Label(hdr, text=label, font=cfg.FONT["xs"],
                     bg=cfg.C("card"), fg=cfg.C("text3")).pack(side="right", anchor="e")
            tk.Label(sc, text=value, font=cfg.FONT["xl_b"],
                     bg=cfg.C("card"), fg=cfg.C("text"), anchor="w").pack(anchor="w", pady=(4, 0))

        # Progress pill
        pc = self._card(strip, padx=14, pady=10)
        pc.grid(row=0, column=5, sticky="nsew")
        strip.columnconfigure(5, weight=1)

        tk.Label(pc, text=f"\U0001f3af  {pct}%", font=cfg.FONT["xl_b"],
                 bg=cfg.C("card"), fg=cfg.C("accent"), anchor="w").pack(anchor="w")
        tk.Label(pc, text="Completion", font=cfg.FONT["xs"],
                 bg=cfg.C("card"), fg=cfg.C("text3"), anchor="w").pack(anchor="w", pady=(2, 6))
        bar_bg = tk.Frame(pc, bg=cfg.C("border"), height=4)
        bar_bg.pack(fill="x")
        tk.Frame(bar_bg, bg=cfg.C("accent"), height=4).place(
            x=0, y=0, relwidth=pct / 100 if pct else 0, height=4
        )

        # ── 3. Three-column section ───────────────────────────────────────
        lower = tk.Frame(self._container, bg=cfg.C("bg"))
        lower.pack(fill="both", expand=True, padx=P, pady=(0, P))
        lower.columnconfigure(0, weight=5)
        lower.columnconfigure(1, weight=3)
        lower.columnconfigure(2, weight=4)

        # --- Pending tasks (col 0) ----------------------------------------
        tc = self._card(lower)
        tc.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(tc, text="Pending Tasks", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=cfg.C("text"), anchor="w",
                 padx=16, pady=10).pack(fill="x")
        make_separator(tc, bg=cfg.C("border")).pack(fill="x", padx=16)

        pending_tasks = store.pending_tasks[:6]
        if pending_tasks:
            for t in pending_tasks:
                trow = tk.Frame(tc, bg=cfg.C("card"), padx=16, pady=5)
                trow.pack(fill="x")

                dot = cfg.PRIORITY_FG.get(t.get("priority", ""), cfg.C("text3"))
                tk.Label(trow, text="\u25cf", font=cfg.FONT["xs"],
                         bg=cfg.C("card"), fg=dot).pack(side="left", padx=(0, 6))
                tk.Label(trow, text=t.get("title", ""), font=cfg.FONT["sm"],
                         bg=cfg.C("card"), fg=cfg.C("text"),
                         anchor="w").pack(side="left", fill="x", expand=True)

                def _done(tid=t["id"]):
                    store.toggle_complete(tid)

                tk.Button(trow, text="\u2713", font=cfg.FONT["xs"],
                          bg=cfg.C("card2"), fg=cfg.C("text3"),
                          activebackground=cfg.C("success"), activeforeground="#fff",
                          relief="flat", bd=0, padx=6, pady=1,
                          cursor="hand2", command=_done).pack(side="right")

                make_separator(tc, bg=cfg.C("border")).pack(fill="x", padx=16)
        else:
            tk.Label(tc, text="All caught up  \U0001f3c6", font=cfg.FONT["sm"],
                     bg=cfg.C("card"), fg=cfg.C("success"),
                     padx=16, pady=14).pack(anchor="w")

        # --- Today's events (col 1) ----------------------------------------
        ec = self._card(lower)
        ec.grid(row=0, column=1, sticky="nsew", padx=6)

        tk.Label(ec, text="Today's Events", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=cfg.C("text"), anchor="w",
                 padx=14, pady=10).pack(fill="x")
        make_separator(ec, bg=cfg.C("border")).pack(fill="x", padx=14)

        if store.today_events:
            for ev in store.today_events:
                erow = tk.Frame(ec, bg=cfg.C("card"), padx=14, pady=8)
                erow.pack(fill="x")
                tk.Label(erow, text=ev.get("time", "\u2014"), font=cfg.FONT["xs_b"],
                         bg=cfg.C("accent2"), fg="#fff",
                         padx=6, pady=2).pack(side="left")
                tk.Label(erow, text=f"  {ev.get('title', '')}",
                         font=cfg.FONT["xs"],
                         bg=cfg.C("card"), fg=cfg.C("text"),
                         wraplength=130, justify="left").pack(side="left")
                make_separator(ec, bg=cfg.C("border")).pack(fill="x", padx=14)
        else:
            tk.Label(ec,
                     text="No events today \U0001f389",
                     font=cfg.FONT["xs"],
                     bg=cfg.C("card"), fg=cfg.C("text2"),
                     padx=14, pady=14).pack(anchor="w", expand=True)

        # --- Recent notes (col 2) ------------------------------------------
        nc = self._card(lower)
        nc.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        tk.Label(nc, text="Recent Notes", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=cfg.C("text"), anchor="w",
                 padx=16, pady=10).pack(fill="x")
        make_separator(nc, bg=cfg.C("border")).pack(fill="x", padx=16)

        recent = sorted(store.notes,
                        key=lambda n: n.get("createdAt", ""), reverse=True)[:4]
        if recent:
            npad = tk.Frame(nc, bg=cfg.C("card"), padx=16, pady=10)
            npad.pack(fill="both", expand=True)
            for note in recent:
                fg_c, bg_c = cfg.color_pair(note.get("color", "violet"))
                chip = tk.Frame(npad, bg=bg_c, padx=10, pady=7,
                                highlightthickness=1, highlightbackground=fg_c)
                chip.pack(fill="x", pady=(0, 6))
                tk.Label(chip, text=note.get("title", ""), font=cfg.FONT["sm_b"],
                         bg=bg_c, fg=fg_c, anchor="w").pack(anchor="w")
                body = note.get("description", "")[:55]
                if body:
                    tk.Label(chip, text=body, font=cfg.FONT["xs"],
                             bg=bg_c, fg=fg_c, anchor="w",
                             wraplength=200, justify="left").pack(anchor="w", pady=(2, 0))
        else:
            tk.Label(nc,
                     text="No notes yet.\nCreate your first one!",
                     font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("text2"),
                     padx=16, pady=14, justify="center").pack(anchor="w", expand=True)

    # ── Actions ──────────────────────────────────────────────────────────────
    def _quick_add(self, _event=None):
        text = self._inline_var.get().strip()
        ph = "Quick-add a task"
        if not text or text.startswith(ph):
            return
        self._store.add_task(
            title=text, priority="Medium",
            dueDate=date.today().isoformat(),
            status="Todo", category="Focus",
        )
        self._inline_var.set("")

    def _on_add_task(self, fields):
        self._store.add_task(**fields)
