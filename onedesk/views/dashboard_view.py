"""
OneDesk Dashboard View — dashboard_view.py
Hero command banner, KPI stat cards, today's schedule, recent notes, pending tasks.
"""

import tkinter as tk
from datetime import date
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_heading, make_label, make_separator,
    ScrollableFrame, make_badge,
)
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

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        # Outer scrollable container
        self._scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        self._scroll.pack(fill="both", expand=True)
        self._container = self._scroll.inner
        self._render()

    def _refresh(self):
        for w in self._container.winfo_children():
            w.destroy()
        self._render()

    def _render(self):
        pad = cfg.PAD
        store = self._store
        today = date.today().isoformat()

        # greeting
        hour = date.today().timetuple().tm_hour
        try:
            import time as _t
            hour = _t.localtime().tm_hour
        except Exception:
            pass
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        name = self._auth.display_name

        # ── Hero banner ───────────────────────────────────────────────────
        hero = tk.Frame(
            self._container,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        hero.pack(fill="x", padx=pad, pady=(pad, 4))

        hero_inner = tk.Frame(hero, bg=cfg.C("card"), padx=24, pady=20)
        hero_inner.pack(fill="both")

        # Status pill
        pill_fg, pill_bg = cfg.color_pair("violet")
        pill = tk.Frame(hero_inner, bg=pill_bg)
        pill.pack(anchor="w", pady=(0, 10))
        tk.Label(pill, text="● LIVE  •  Synced", font=cfg.FONT["xs"],
                 bg=pill_bg, fg=pill_fg, padx=10, pady=3).pack()

        tk.Label(
            hero_inner,
            text=f"{greeting}, {name}! 👋",
            font=cfg.FONT["2xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(anchor="w")

        tk.Label(
            hero_inner,
            text=f"Today is {date.today().strftime('%A, %B %d %Y')}. Let's make it count.",
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(4, 12))

        # Quick inline task adder
        inline_frame = tk.Frame(hero_inner, bg=cfg.C("card"))
        inline_frame.pack(fill="x")
        self._inline_var = tk.StringVar()
        inline_entry = tk.Entry(
            inline_frame,
            textvariable=self._inline_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        inline_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        inline_entry.insert(0, "Quick-add a task…")
        inline_entry.configure(fg=cfg.C("text3"))

        def _focus_in(e):
            if inline_entry.get() == "Quick-add a task…":
                inline_entry.delete(0, "end")
                inline_entry.configure(fg=cfg.C("text"))
        def _focus_out(e):
            if not inline_entry.get():
                inline_entry.insert(0, "Quick-add a task…")
                inline_entry.configure(fg=cfg.C("text3"))
        inline_entry.bind("<FocusIn>",  _focus_in)
        inline_entry.bind("<FocusOut>", _focus_out)
        inline_entry.bind("<Return>", self._quick_add)

        make_button(inline_frame, text="Add", command=self._quick_add, variant="primary").pack(side="left")
        make_button(
            inline_frame, text="+ Detailed",
            command=lambda: TaskDialog(self, self._on_add_task),
            variant="secondary"
        ).pack(side="left", padx=(8, 0))

        # ── KPI stat cards ────────────────────────────────────────────────
        stat_row = tk.Frame(self._container, bg=cfg.C("bg"))
        stat_row.pack(fill="x", padx=pad, pady=8)

        completed = len(store.completed_tasks)
        total     = len(store.tasks)
        pct       = store.completion_pct
        pending   = len(store.pending_tasks)

        stats = [
            ("📋", "Total Tasks",   str(total),         cfg.C("accent")),
            ("✅", "Completed",     str(completed),     cfg.C("success")),
            ("⏳", "Pending",       str(pending),       cfg.C("warn")),
            ("📝", "Notes",         str(len(store.notes)),  cfg.C("accent2")),
            ("📅", "Events Today",  str(len(store.today_events)), cfg.C("accent3")),
            ("🎯", "Completion",    f"{pct}%",           cfg.C("text")),
        ]
        for i, (icon, title, value, color) in enumerate(stats):
            card = tk.Frame(
                stat_row,
                bg=cfg.C("card"),
                highlightthickness=1,
                highlightbackground=cfg.C("border"),
                padx=16,
                pady=14,
            )
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            stat_row.columnconfigure(i, weight=1)

            tk.Label(card, text=icon, font=cfg.FONT["xl"],
                     bg=cfg.C("card"), fg=color).pack(anchor="w")
            tk.Label(card, text=value, font=cfg.FONT["xl_b"],
                     bg=cfg.C("card"), fg=cfg.C("text")).pack(anchor="w")
            tk.Label(card, text=title, font=cfg.FONT["xs"],
                     bg=cfg.C("card"), fg=cfg.C("text2")).pack(anchor="w")

        # ── Progress bar ──────────────────────────────────────────────────
        prog_frame = tk.Frame(self._container, bg=cfg.C("card"),
                              highlightthickness=1, highlightbackground=cfg.C("border"))
        prog_frame.pack(fill="x", padx=pad, pady=4)
        inner = tk.Frame(prog_frame, bg=cfg.C("card"), padx=20, pady=12)
        inner.pack(fill="x")
        tk.Label(inner, text=f"Overall Progress — {pct}%", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=cfg.C("text")).pack(anchor="w", pady=(0, 6))
        bar_bg = tk.Frame(inner, bg=cfg.C("border"), height=8)
        bar_bg.pack(fill="x")
        bar_bg.update_idletasks()
        fill_w = int(bar_bg.winfo_reqwidth() * pct / 100) if pct else 0
        tk.Frame(bar_bg, bg=cfg.C("accent"), height=8, width=fill_w).place(x=0, y=0, relwidth=pct/100, height=8)

        # ── Two column layout: Schedule | Recent Notes ─────────────────
        two_col = tk.Frame(self._container, bg=cfg.C("bg"))
        two_col.pack(fill="both", expand=True, padx=pad, pady=8)
        two_col.columnconfigure(0, weight=1)
        two_col.columnconfigure(1, weight=1)

        # Today's schedule
        sched_frame = tk.Frame(two_col, bg=cfg.C("card"),
                                highlightthickness=1, highlightbackground=cfg.C("border"))
        sched_frame.grid(row=0, column=0, padx=(0, 4), sticky="nsew", pady=2)
        tk.Label(sched_frame, text="📅  Today's Schedule", font=cfg.FONT["md_b"],
                 bg=cfg.C("card"), fg=cfg.C("text"), anchor="w", padx=16, pady=12).pack(fill="x")
        make_separator(sched_frame, bg=cfg.C("border")).pack(fill="x", padx=16)

        if store.today_events:
            for ev in store.today_events:
                erow = tk.Frame(sched_frame, bg=cfg.C("card"), padx=16, pady=6)
                erow.pack(fill="x")
                tk.Label(erow, text=ev.get("time", "—"), font=cfg.FONT["xs_b"],
                         bg=cfg.C("accent2"), fg="#fff", padx=6, pady=2).pack(side="left")
                tk.Label(erow, text=f"  {ev.get('title', '')}", font=cfg.FONT["sm"],
                         bg=cfg.C("card"), fg=cfg.C("text")).pack(side="left")
        else:
            tk.Label(sched_frame, text="No events today 🎉", font=cfg.FONT["sm"],
                     bg=cfg.C("card"), fg=cfg.C("text2"), padx=16, pady=12).pack(anchor="w")

        # Pending tasks
        tasks_frame = tk.Frame(two_col, bg=cfg.C("card"),
                                highlightthickness=1, highlightbackground=cfg.C("border"))
        tasks_frame.grid(row=0, column=1, padx=(4, 0), sticky="nsew", pady=2)
        tk.Label(tasks_frame, text="✔  Pending Tasks", font=cfg.FONT["md_b"],
                 bg=cfg.C("card"), fg=cfg.C("text"), anchor="w", padx=16, pady=12).pack(fill="x")
        make_separator(tasks_frame, bg=cfg.C("border")).pack(fill="x", padx=16)

        pending_tasks = store.pending_tasks[:6]
        if pending_tasks:
            for t in pending_tasks:
                trow = tk.Frame(tasks_frame, bg=cfg.C("card"), padx=16, pady=5)
                trow.pack(fill="x")
                # Checkbox-style toggle
                done_var = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(
                    trow,
                    variable=done_var,
                    bg=cfg.C("card"),
                    activebackground=cfg.C("card"),
                    command=lambda tid=t["id"]: store.toggle_complete(tid),
                )
                chk.pack(side="left")
                tk.Label(trow, text=t.get("title", ""), font=cfg.FONT["sm"],
                         bg=cfg.C("card"), fg=cfg.C("text")).pack(side="left")
                pcolor = cfg.PRIORITY_FG.get(t.get("priority", ""), cfg.C("text2"))
                tk.Label(trow, text=t.get("priority", ""), font=cfg.FONT["xs"],
                         bg=cfg.C("card"), fg=pcolor).pack(side="right")
        else:
            tk.Label(tasks_frame, text="All tasks done! 🏆", font=cfg.FONT["sm"],
                     bg=cfg.C("card"), fg=cfg.C("success"), padx=16, pady=12).pack(anchor="w")

        # ── Recent Notes ──────────────────────────────────────────────────
        rn_frame = tk.Frame(self._container, bg=cfg.C("card"),
                             highlightthickness=1, highlightbackground=cfg.C("border"))
        rn_frame.pack(fill="x", padx=pad, pady=(4, pad))
        tk.Label(rn_frame, text="📝  Recent Notes", font=cfg.FONT["md_b"],
                 bg=cfg.C("card"), fg=cfg.C("text"), anchor="w", padx=16, pady=12).pack(fill="x")
        make_separator(rn_frame, bg=cfg.C("border")).pack(fill="x", padx=16)

        recent = sorted(store.notes, key=lambda n: n.get("createdAt", ""), reverse=True)[:4]
        if recent:
            grid = tk.Frame(rn_frame, bg=cfg.C("card"), padx=16, pady=10)
            grid.pack(fill="x")
            for i, note in enumerate(recent):
                fg, bg = cfg.color_pair(note.get("color", "violet"))
                chip = tk.Frame(grid, bg=bg, padx=12, pady=8,
                                highlightthickness=1, highlightbackground=fg)
                chip.grid(row=0, column=i, padx=4, sticky="nsew")
                grid.columnconfigure(i, weight=1)
                tk.Label(chip, text=note.get("title", ""), font=cfg.FONT["sm_b"],
                         bg=bg, fg=fg, anchor="w").pack(anchor="w")
                tk.Label(chip, text=note.get("description", "")[:80],
                         font=cfg.FONT["xs"], bg=bg, fg=fg, anchor="w",
                         wraplength=220).pack(anchor="w")
        else:
            tk.Label(rn_frame, text="No notes yet. Create your first note!", font=cfg.FONT["sm"],
                     bg=cfg.C("card"), fg=cfg.C("text2"), padx=16, pady=12).pack(anchor="w")

    # ── Quick add ────────────────────────────────────────────────────────────
    def _quick_add(self, _event=None):
        text = self._inline_var.get().strip()
        if not text or text == "Quick-add a task…":
            return
        self._store.add_task(
            title=text,
            priority="Medium",
            dueDate=date.today().isoformat(),
            status="Todo",
            category="Focus",
        )
        self._inline_var.set("")

    def _on_add_task(self, fields):
        self._store.add_task(**fields)
