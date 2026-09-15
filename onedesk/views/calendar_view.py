"""
OneDesk Calendar View — calendar_view.py
Month, Week, and Day views with event/task markers and new-event dialog.
"""

import tkinter as tk
from datetime import date, timedelta
from .. import config as cfg
from ..components.ui_helpers import make_button, make_separator, ScrollableFrame
from ..components.modals import EventDialog, confirm

WEEKDAYS  = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTHS    = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def _month_days(year: int, month: int):
    """Return list of date objects for all cells in a month calendar grid."""
    first = date(year, month, 1)
    # pad to start on Sunday
    start = first - timedelta(days=first.weekday() + 1) if first.weekday() != 6 else first
    # adjust: weekday() gives Mon=0, so Sunday = 6
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    days = []
    d = start
    while len(days) < 42:
        days.append(d)
        d += timedelta(days=1)
    return days


class CalendarView(tk.Frame):
    def __init__(self, parent, store, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store  = store
        self._cursor = date.today()
        self._view   = "month"   # "month" | "week" | "day"

        self._store.subscribe(self._refresh)
        self._build()

    def destroy(self):
        self._store.unsubscribe(self._refresh)
        super().destroy()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        self._header = tk.Frame(self, bg=cfg.C("bg"))
        self._header.pack(fill="x", padx=cfg.PAD, pady=cfg.PAD)
        self._render_header()

        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=cfg.PAD)

        self._body = tk.Frame(self, bg=cfg.C("bg"))
        self._body.pack(fill="both", expand=True, padx=cfg.PAD, pady=cfg.PAD)
        self._render_view()

    def _render_header(self):
        for w in self._header.winfo_children():
            w.destroy()

        row = tk.Frame(self._header, bg=cfg.C("bg"))
        row.pack(fill="x")

        tk.Label(row, text="Calendar", font=cfg.FONT["2xl_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text")).pack(side="left")

        # Nav buttons
        right = tk.Frame(row, bg=cfg.C("bg"))
        right.pack(side="right")

        make_button(right, "← Prev", command=self._prev, variant="ghost").pack(side="left", padx=2)
        make_button(right, "Today",  command=self._today, variant="secondary").pack(side="left", padx=2)
        make_button(right, "Next →", command=self._next, variant="ghost").pack(side="left", padx=2)

        make_button(right, "+ Event", command=lambda: EventDialog(
            self, self._on_add_event, default_date=self._cursor.isoformat()
        ), variant="primary").pack(side="left", padx=(12, 0))

        # View mode tabs
        tabs = tk.Frame(self._header, bg=cfg.C("bg"))
        tabs.pack(anchor="w", pady=(8, 0))
        for label in ["month", "week", "day"]:
            active = label == self._view
            tk.Button(
                tabs, text=label.capitalize(), font=cfg.FONT["xs_b"],
                fg=cfg.C("text") if active else cfg.C("text2"),
                bg=cfg.C("accent") if active else cfg.C("card2"),
                activeforeground=cfg.C("text"), activebackground=cfg.C("accent"),
                relief="flat", bd=0, padx=10, pady=3, cursor="hand2",
                command=lambda v=label: self._set_view(v),
            ).pack(side="left", padx=2)

        # Current period label
        self._period_label = tk.Label(
            self._header, text=self._period_text(),
            font=cfg.FONT["lg_b"], bg=cfg.C("bg"), fg=cfg.C("text"),
        )
        self._period_label.pack(anchor="w", pady=(6, 0))

    def _period_text(self) -> str:
        c = self._cursor
        if self._view == "month":
            return f"{MONTHS[c.month - 1]} {c.year}"
        elif self._view == "week":
            start = c - timedelta(days=c.weekday() + 1) % 7
            if start.weekday() != 6:
                start = c - timedelta(days=(c.weekday() + 1) % 7)
            end = start + timedelta(days=6)
            return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
        else:
            return c.strftime("%A, %B %d %Y")

    def _refresh(self):
        self._render_header()
        self._render_view()

    def _render_view(self):
        for w in self._body.winfo_children():
            w.destroy()
        if self._view == "month":
            self._render_month()
        elif self._view == "week":
            self._render_week()
        else:
            self._render_day()

    # ── Month view ───────────────────────────────────────────────────────────
    def _render_month(self):
        grid = tk.Frame(self._body, bg=cfg.C("bg"))
        grid.pack(fill="both", expand=True)

        # Weekday headers
        for col, day in enumerate(WEEKDAYS):
            tk.Label(grid, text=day, font=cfg.FONT["xs_b"],
                     bg=cfg.C("bg"), fg=cfg.C("text3"),
                     width=10, anchor="center").grid(row=0, column=col, padx=1, pady=(0, 4))
            grid.columnconfigure(col, weight=1)

        today = date.today()
        days  = _month_days(self._cursor.year, self._cursor.month)

        for idx, d in enumerate(days):
            row, col = divmod(idx, 7)
            is_today    = (d == today)
            is_cur_mon  = (d.month == self._cursor.month)
            items       = self._items_on(d.isoformat())

            cell = tk.Frame(
                grid,
                bg=cfg.C("card2") if is_today else cfg.C("card"),
                highlightthickness=1,
                highlightbackground=cfg.C("accent") if is_today else cfg.C("border"),
                padx=4, pady=4,
            )
            cell.grid(row=row + 1, column=col, padx=2, pady=2, sticky="nsew")
            grid.rowconfigure(row + 1, weight=1)

            # Day number
            day_color = cfg.C("accent") if is_today else (cfg.C("text") if is_cur_mon else cfg.C("text3"))
            num_lbl = tk.Label(
                cell, text=str(d.day), font=cfg.FONT["xs_b"],
                bg=cell["bg"], fg=day_color, anchor="nw",
            )
            num_lbl.pack(anchor="nw")
            # Click to add event
            cell.bind("<Button-1>", lambda e, dd=d.isoformat(): EventDialog(
                self, self._on_add_event, default_date=dd))
            num_lbl.bind("<Button-1>", lambda e, dd=d.isoformat(): EventDialog(
                self, self._on_add_event, default_date=dd))

            # Event dots
            for item in items[:3]:
                dot_color = cfg.C("accent3") if item.get("isTask") else cfg.C("accent")
                dot_row = tk.Frame(cell, bg=cell["bg"])
                dot_row.pack(anchor="w", fill="x")
                tk.Frame(dot_row, bg=dot_color, width=6, height=6).pack(side="left", padx=(0, 4))
                tk.Label(dot_row, text=item.get("title", "")[:14], font=cfg.FONT["xs"],
                         bg=cell["bg"], fg=cfg.C("text" if is_cur_mon else "text3")).pack(side="left")

            if len(items) > 3:
                tk.Label(cell, text=f"+{len(items)-3} more", font=cfg.FONT["xs"],
                         bg=cell["bg"], fg=cfg.C("text2")).pack(anchor="w")

    # ── Week view ────────────────────────────────────────────────────────────
    def _render_week(self):
        c = self._cursor
        # get Sunday start
        start = c - timedelta(days=(c.weekday() + 1) % 7)
        week  = [start + timedelta(days=i) for i in range(7)]
        today = date.today()

        grid = tk.Frame(self._body, bg=cfg.C("bg"))
        grid.pack(fill="both", expand=True)

        for col, d in enumerate(week):
            is_today = (d == today)
            grid.columnconfigure(col, weight=1)
            hdr = tk.Frame(grid, bg=cfg.C("card2") if is_today else cfg.C("card"),
                            padx=8, pady=6)
            hdr.grid(row=0, column=col, padx=2, sticky="ew")
            tk.Label(hdr, text=WEEKDAYS[col], font=cfg.FONT["xs_b"],
                     bg=hdr["bg"], fg=cfg.C("text3")).pack()
            num_fg = cfg.C("accent") if is_today else cfg.C("text")
            tk.Label(hdr, text=str(d.day), font=cfg.FONT["lg_b"],
                     bg=hdr["bg"], fg=num_fg).pack()

            cell = tk.Frame(grid, bg=cfg.C("card"),
                             highlightthickness=1,
                             highlightbackground=cfg.C("accent") if is_today else cfg.C("border"))
            cell.grid(row=1, column=col, padx=2, pady=2, sticky="nsew")
            grid.rowconfigure(1, weight=1)

            items = self._items_on(d.isoformat())
            scroll = ScrollableFrame(cell, bg=cfg.C("card"))
            scroll.pack(fill="both", expand=True)
            for item in items:
                dot = cfg.C("accent3") if item.get("isTask") else cfg.C("accent2")
                row = tk.Frame(scroll.inner, bg=cfg.C("card"), padx=6, pady=3)
                row.pack(fill="x")
                tk.Frame(row, bg=dot, width=3).pack(side="left", fill="y")
                txt = tk.Frame(row, bg=cfg.C("card"), padx=4)
                txt.pack(side="left", fill="x", expand=True)
                if item.get("time"):
                    tk.Label(txt, text=item["time"], font=cfg.FONT["xs"],
                             bg=cfg.C("card"), fg=cfg.C("text3")).pack(anchor="w")
                tk.Label(txt, text=item.get("title", ""), font=cfg.FONT["xs_b"],
                         bg=cfg.C("card"), fg=cfg.C("text"), wraplength=100).pack(anchor="w")
            cell.bind("<Button-1>", lambda e, dd=d.isoformat(): EventDialog(
                self, self._on_add_event, default_date=dd))

    # ── Day view ─────────────────────────────────────────────────────────────
    def _render_day(self):
        d    = self._cursor
        items = self._items_on(d.isoformat())

        scroll = ScrollableFrame(self._body, bg=cfg.C("bg"))
        scroll.pack(fill="both", expand=True)
        inner = scroll.inner

        if not items:
            tk.Label(inner, text="No events or tasks on this day.",
                     font=cfg.FONT["md"], bg=cfg.C("bg"), fg=cfg.C("text2"), pady=30).pack()
            make_button(inner, "+ Add Event", command=lambda: EventDialog(
                self, self._on_add_event, default_date=d.isoformat()
            ), variant="primary").pack(pady=8)
            return

        for item in sorted(items, key=lambda i: i.get("time", "")):
            card = tk.Frame(inner, bg=cfg.C("card"),
                             highlightthickness=1, highlightbackground=cfg.C("border"))
            card.pack(fill="x", pady=4)
            row = tk.Frame(card, bg=cfg.C("card"), padx=16, pady=12)
            row.pack(fill="x")

            accent = cfg.C("accent3") if item.get("isTask") else cfg.C("accent2")
            tk.Frame(card, bg=accent, width=3).place(relx=0, rely=0, relheight=1)

            lbl = "[Task]" if item.get("isTask") else ""
            tk.Label(row, text=f"{item.get('time', '--:--')}  {lbl}",
                     font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text3")).pack(anchor="w")
            tk.Label(row, text=item.get("title", ""), font=cfg.FONT["md_b"],
                     bg=cfg.C("card"), fg=cfg.C("text")).pack(anchor="w")
            if item.get("description"):
                tk.Label(row, text=item["description"], font=cfg.FONT["xs"],
                         bg=cfg.C("card"), fg=cfg.C("text2"), wraplength=500).pack(anchor="w", pady=(2, 0))

            if not item.get("isTask"):
                btn_r = tk.Frame(row, bg=cfg.C("card"))
                btn_r.pack(anchor="w", pady=(6, 0))
                tk.Button(btn_r, text="Edit", font=cfg.FONT["xs"], bg=cfg.C("card2"),
                          fg=cfg.C("text"), relief="flat", cursor="hand2",
                          command=lambda ev=item: EventDialog(
                              self, lambda f, eid=ev["id"]: self._store.update_event(eid, **f),
                              event=ev)).pack(side="left", padx=2)
                tk.Button(btn_r, text="Delete", font=cfg.FONT["xs"], bg=cfg.C("card"),
                          fg=cfg.C("danger"), relief="flat", cursor="hand2",
                          command=lambda ev=item: confirm(
                              self, f"Delete '{ev['title']}'?",
                              lambda eid=ev["id"]: self._store.delete_event(eid)
                          )).pack(side="left", padx=2)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _items_on(self, date_str: str) -> list:
        events    = [dict(e, isTask=False) for e in self._store.events if e.get("date") == date_str]
        task_evs  = [
            {"id": f"task-{t['id']}", "title": t["title"], "date": t.get("dueDate"),
             "time": "", "isTask": True, "priority": t.get("priority")}
            for t in self._store.tasks if t.get("dueDate") == date_str
        ]
        return sorted(events + task_evs, key=lambda i: i.get("time", ""))

    def _on_add_event(self, fields):
        self._store.add_event(**fields)

    def _prev(self):
        if self._view == "month":
            m = self._cursor.month - 1
            y = self._cursor.year
            if m == 0:
                m, y = 12, y - 1
            self._cursor = self._cursor.replace(year=y, month=m, day=1)
        elif self._view == "week":
            self._cursor -= timedelta(weeks=1)
        else:
            self._cursor -= timedelta(days=1)
        self._refresh()

    def _next(self):
        if self._view == "month":
            m = self._cursor.month + 1
            y = self._cursor.year
            if m == 13:
                m, y = 1, y + 1
            self._cursor = self._cursor.replace(year=y, month=m, day=1)
        elif self._view == "week":
            self._cursor += timedelta(weeks=1)
        else:
            self._cursor += timedelta(days=1)
        self._refresh()

    def _today(self):
        self._cursor = date.today()
        self._refresh()

    def _set_view(self, v: str):
        self._view = v
        self._refresh()
