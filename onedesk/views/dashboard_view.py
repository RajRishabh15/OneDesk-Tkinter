"""
OneDesk Dashboard View — dashboard_view.py
Minimal, modern home dashboard: greeting, live stats, progress,
today's tasks, today's events, and a recent-notes strip.
"""

import tkinter as tk
import time
from datetime import date
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_separator, ScrollableFrame,
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
        self._scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        self._scroll.pack(fill="both", expand=True)
        self._container = self._scroll.inner
        self._render()

    def _refresh(self):
        for w in self._container.winfo_children():
            w.destroy()
        self._render()

    # ── Helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _greeting():
        h = time.localtime().tm_hour
        if h < 12:   return "Good morning"
        if h < 17:   return "Good afternoon"
        return "Good evening"

    def _card(self, parent, **kw):
        """Return a styled card frame."""
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", cfg.C("border"))
        return tk.Frame(parent, **kw)

    def _section_header(self, parent, text: str):
        tk.Label(
            parent, text=text,
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"),
            anchor="w", padx=18, pady=10,
        ).pack(fill="x")
        make_separator(parent, bg=cfg.C("border")).pack(fill="x", padx=18)

    # ── Render ───────────────────────────────────────────────────────────────
    def _render(self):
        P   = 16   # outer padding
        store = self._store
        today = date.today()

        # ── 1. Greeting header ────────────────────────────────────────────
        header = tk.Frame(self._container, bg=cfg.C("bg"))
        header.pack(fill="x", padx=P, pady=(P, 4))

        name = self._auth.display_name or "there"
        tk.Label(
            header,
            text=f"{self._greeting()}, {name} 👋",
            font=cfg.FONT["2xl_b"],
            bg=cfg.C("bg"), fg=cfg.C("text"),
            anchor="w",
        ).pack(side="left", anchor="s")

        date_lbl = tk.Label(
            header,
            text=today.strftime("%A, %B %d"),
            font=cfg.FONT["sm"],
            bg=cfg.C("bg"), fg=cfg.C("text3"),
            anchor="e",
        )
        date_lbl.pack(side="right", anchor="s", pady=(0, 3))

        # ── 2. Quick-add task bar ─────────────────────────────────────────
        qa_row = self._card(self._container, padx=0)
        qa_row.pack(fill="x", padx=P, pady=(4, 8))

        qa_inner = tk.Frame(qa_row, bg=cfg.C("card"), padx=18, pady=12)
        qa_inner.pack(fill="x")

        self._inline_var = tk.StringVar()
        _PH = "Add a task… (press Enter)"

        qa_entry = tk.Entry(
            qa_inner,
            textvariable=self._inline_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
            insertbackground=cfg.C("text"),
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        qa_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))
        qa_entry.insert(0, _PH)

        def _fi(e):
            if qa_entry.get() == _PH:
                qa_entry.delete(0, "end")
                qa_entry.configure(fg=cfg.C("text"))
            qa_entry.configure(highlightbackground=cfg.C("accent"))

        def _fo(e):
            if not qa_entry.get():
                qa_entry.insert(0, _PH)
                qa_entry.configure(fg=cfg.C("text3"))
            qa_entry.configure(highlightbackground=cfg.C("border"))

        qa_entry.bind("<FocusIn>",  _fi)
        qa_entry.bind("<FocusOut>", _fo)
        qa_entry.bind("<Return>",   self._quick_add)

        make_button(qa_inner, text="Add", command=self._quick_add, variant="primary").pack(side="left")
        make_button(
            qa_inner, text="+ Detailed",
            command=lambda: TaskDialog(self, self._on_add_task),
            variant="secondary"
        ).pack(side="left", padx=(8, 0))

        # ── 3. Stat strip (4 cards) ───────────────────────────────────────
        total     = len(store.tasks)
        completed = len(store.completed_tasks)
        pending   = len(store.pending_tasks)
        pct       = store.completion_pct

        stat_row = tk.Frame(self._container, bg=cfg.C("bg"))
        stat_row.pack(fill="x", padx=P, pady=(0, 8))

        stats = [
            ("Total Tasks",  str(total),      cfg.C("accent"),  "📋"),
            ("Completed",    str(completed),   cfg.C("success"), "✅"),
            ("Pending",      str(pending),     cfg.C("warn"),    "⏳"),
            ("Notes",        str(len(store.notes)), cfg.C("accent2"), "📝"),
        ]
        for i, (label, value, color, icon) in enumerate(stats):
            card = self._card(stat_row, padx=20, pady=14)
            card.grid(row=0, column=i, padx=(0 if i == 0 else 6, 0), sticky="nsew")
            stat_row.columnconfigure(i, weight=1)

            top = tk.Frame(card, bg=cfg.C("card"))
            top.pack(fill="x")
            tk.Label(top, text=icon, font=cfg.FONT["base"], bg=cfg.C("card"), fg=color).pack(side="left")
            tk.Label(top, text=label, font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("text3")).pack(
                side="right", anchor="e", pady=2
            )
            tk.Label(card, text=value, font=cfg.FONT["2xl_b"], bg=cfg.C("card"), fg=cfg.C("text"),
                     anchor="w").pack(anchor="w", pady=(4, 0))

        # ── 4. Progress bar (slim) ────────────────────────────────────────
        prog_card = self._card(self._container)
        prog_card.pack(fill="x", padx=P, pady=(0, 10))
        prog_inner = tk.Frame(prog_card, bg=cfg.C("card"), padx=18, pady=12)
        prog_inner.pack(fill="x")

        prog_top = tk.Frame(prog_inner, bg=cfg.C("card"))
        prog_top.pack(fill="x", pady=(0, 8))
        tk.Label(prog_top, text="Task completion", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=cfg.C("text")).pack(side="left")
        tk.Label(prog_top, text=f"{pct}%", font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=cfg.C("accent")).pack(side="right")

        bar_bg = tk.Frame(prog_inner, bg=cfg.C("border"), height=6)
        bar_bg.pack(fill="x")
        # draw fill with relwidth so it scales on resize
        fill = tk.Frame(bar_bg, bg=cfg.C("accent"), height=6)
        fill.place(x=0, y=0, relwidth=pct / 100 if pct else 0, height=6)

        # ── 5. Two-column lower: Pending tasks | Today's events ───────────
        lower = tk.Frame(self._container, bg=cfg.C("bg"))
        lower.pack(fill="both", expand=True, padx=P, pady=(0, 8))
        lower.columnconfigure(0, weight=3)
        lower.columnconfigure(1, weight=2)

        # ── Pending tasks ─────────────────────────────────────────────────
        tasks_card = self._card(lower)
        tasks_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._section_header(tasks_card, "Pending tasks")

        pending_tasks = store.pending_tasks[:7]
        if pending_tasks:
            for t in pending_tasks:
                row = tk.Frame(tasks_card, bg=cfg.C("card"), padx=18, pady=6)
                row.pack(fill="x")

                # Priority dot
                dot_color = cfg.PRIORITY_FG.get(t.get("priority", ""), cfg.C("text3"))
                tk.Label(row, text="●", font=cfg.FONT["xs"], bg=cfg.C("card"),
                         fg=dot_color).pack(side="left", padx=(0, 8))

                tk.Label(row, text=t.get("title", ""), font=cfg.FONT["sm"],
                         bg=cfg.C("card"), fg=cfg.C("text"), anchor="w").pack(side="left", fill="x", expand=True)

                # Done button
                def _mark(tid=t["id"]):
                    store.toggle_complete(tid)

                tk.Button(
                    row, text="✓",
                    font=cfg.FONT["xs"],
                    bg=cfg.C("card2"), fg=cfg.C("text3"),
                    activebackground=cfg.C("success"),
                    activeforeground="#fff",
                    relief="flat", bd=0, padx=6, pady=1,
                    cursor="hand2",
                    command=_mark,
                ).pack(side="right")

                make_separator(tasks_card, bg=cfg.C("border")).pack(fill="x", padx=18)
        else:
            tk.Label(tasks_card, text="All caught up  🏆", font=cfg.FONT["sm"],
                     bg=cfg.C("card"), fg=cfg.C("success"), padx=18, pady=16).pack(anchor="w")

        # ── Today's events ────────────────────────────────────────────────
        events_card = self._card(lower)
        events_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._section_header(events_card, "Today's events")

        if store.today_events:
            for ev in store.today_events:
                row = tk.Frame(events_card, bg=cfg.C("card"), padx=18, pady=8)
                row.pack(fill="x")
                tk.Label(
                    row, text=ev.get("time", "—"),
                    font=cfg.FONT["xs_b"],
                    bg=cfg.C("accent2"), fg="#fff",
                    padx=7, pady=2,
                ).pack(side="left")
                tk.Label(row, text=f"  {ev.get('title', '')}", font=cfg.FONT["sm"],
                         bg=cfg.C("card"), fg=cfg.C("text")).pack(side="left")
                make_separator(events_card, bg=cfg.C("border")).pack(fill="x", padx=18)
        else:
            tk.Label(events_card, text="No events today 🎉", font=cfg.FONT["sm"],
                     bg=cfg.C("card"), fg=cfg.C("text2"), padx=18, pady=16).pack(anchor="w")

        # ── 6. Recent Notes strip ─────────────────────────────────────────
        notes_card = self._card(self._container)
        notes_card.pack(fill="x", padx=P, pady=(0, P))
        self._section_header(notes_card, "Recent notes")

        recent = sorted(store.notes, key=lambda n: n.get("createdAt", ""), reverse=True)[:4]
        if recent:
            grid_frame = tk.Frame(notes_card, bg=cfg.C("card"), padx=18, pady=12)
            grid_frame.pack(fill="x")
            for i, note in enumerate(recent):
                fg, bg = cfg.color_pair(note.get("color", "violet"))
                chip = tk.Frame(grid_frame, bg=bg, padx=14, pady=10,
                                highlightthickness=1, highlightbackground=fg)
                chip.grid(row=0, column=i, padx=(0 if i == 0 else 8, 0), sticky="nsew")
                grid_frame.columnconfigure(i, weight=1)
                tk.Label(chip, text=note.get("title", ""), font=cfg.FONT["sm_b"],
                         bg=bg, fg=fg, anchor="w").pack(anchor="w")
                body = note.get("description", "")[:70]
                if body:
                    tk.Label(chip, text=body, font=cfg.FONT["xs"],
                             bg=bg, fg=fg, anchor="w", wraplength=180,
                             justify="left").pack(anchor="w", pady=(3, 0))
        else:
            tk.Label(notes_card, text="No notes yet — create your first one!",
                     font=cfg.FONT["sm"], bg=cfg.C("card"), fg=cfg.C("text2"),
                     padx=18, pady=16).pack(anchor="w")

    # ── Quick add ────────────────────────────────────────────────────────────
    def _quick_add(self, _event=None):
        text = self._inline_var.get().strip()
        if not text or text.startswith("Add a task"):
            return
        self._store.add_task(
            title=text, priority="Medium",
            dueDate=date.today().isoformat(),
            status="Todo", category="Focus",
        )
        self._inline_var.set("")

    def _on_add_task(self, fields):
        self._store.add_task(**fields)


