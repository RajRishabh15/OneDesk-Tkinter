"""
OneDesk Modern Calendar View — calendar_view.py
State-of-the-art desktop calendar experience:
- Clean, balanced, geometric month grid with pixel-perfect uniform cell sizing
- Streamlined unified header toolbar eliminating visual clutter
- Segmented view capsule (Month, Week, Day, Agenda)
- Interactive slide-out Day Agenda with direct event management
- Modern event chips with clean typography and priority badges
- Full theme synchronization across Dark, Rose, Aqua, and Light modes
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import date, datetime, timedelta
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_separator, make_pill_badge, ScrollableFrame, RoundIconButton,
)
from ..components.modals import EventDialog, confirm
from ..importers import parse_events_file

WEEKDAYS       = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
WEEKDAYS_SHORT = ["S", "M", "T", "W", "T", "F", "S"]
MONTHS         = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _month_days(year: int, month: int):
    """Return list of 42 date objects for the 6-row monthly calendar grid."""
    first = date(year, month, 1)
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
        self._store = store
        self._cursor = date.today()
        self._selected_date = date.today()
        self._view = "month"          # "month" | "week" | "day" | "agenda"
        self._filter_type = "all"     # "all" | "events" | "tasks"
        self._search_query = ""
        self._show_sidebar = False    # default clean full calendar, toggleable with "📋 Agenda Panel"

        self._store.subscribe(self._refresh)
        self._build()

    def destroy(self):
        self._store.unsubscribe(self._refresh)
        super().destroy()

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build(self):
        # 1. Clean Unified Header Toolbar
        self._header = tk.Frame(self, bg=cfg.C("bg"))
        self._header.pack(fill="x", padx=cfg.PAD, pady=(cfg.PAD, 8))
        self._render_header()

        # 2. Main Body (Split View)
        self._split_container = tk.Frame(self, bg=cfg.C("bg"))
        self._split_container.pack(fill="both", expand=True, padx=cfg.PAD, pady=(0, cfg.PAD))

        # Main Calendar Canvas
        self._main_content = tk.Frame(self._split_container, bg=cfg.C("bg"))
        self._main_content.pack(side="left", fill="both", expand=True)

        # Right Slide-Out Sidebar (Day Agenda Drawer)
        self._sidebar = tk.Frame(
            self._split_container,
            bg=cfg.C("card"),
            width=300,
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=14,
            pady=12,
        )
        self._sidebar.pack_propagate(False)

        self._render_sidebar()
        self._render_view()

    # ── Clean, Streamlined Header Bar ─────────────────────────────────────────
    def _render_header(self):
        for w in self._header.winfo_children():
            w.destroy()

        bar = tk.Frame(self._header, bg=cfg.C("bg"))
        bar.pack(fill="x")

        # ── Left: Title & Month Navigation ────────────────────────────────────
        left_box = tk.Frame(bar, bg=cfg.C("bg"))
        left_box.pack(side="left")

        tk.Label(
            left_box,
            text="📅  Calendar",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(side="left", padx=(0, 14))

        # Segmented Nav: ‹  Today  ›
        nav_capsule = tk.Frame(
            left_box,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=2,
            pady=2,
        )
        nav_capsule.pack(side="left", padx=(0, 12))

        tk.Button(
            nav_capsule,
            text="‹",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            activebackground=cfg.C("accent"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self._prev,
        ).pack(side="left")

        tk.Button(
            nav_capsule,
            text="Today",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
            activebackground=cfg.C("accent"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._today,
        ).pack(side="left", padx=2)

        tk.Button(
            nav_capsule,
            text="›",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            activebackground=cfg.C("accent"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=2,
            cursor="hand2",
            command=self._next,
        ).pack(side="left")

        # Period Header (e.g. October 2026)
        tk.Label(
            left_box,
            text=self._period_text(),
            font=cfg.FONT["lg_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(side="left")

        # ── Right: View Capsule, Filter, Actions, Agenda Drawer ────────────────
        right_box = tk.Frame(bar, bg=cfg.C("bg"))
        right_box.pack(side="right")

        # 1. Segmented View Capsule: Month | Week | Day | Agenda
        view_capsule = tk.Frame(
            right_box,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=2,
            pady=2,
        )
        view_capsule.pack(side="left", padx=(0, 10))

        views = [
            ("month", "Month"),
            ("week", "Week"),
            ("day", "Day"),
            ("agenda", "Agenda"),
        ]
        for v_key, v_label in views:
            is_active = (self._view == v_key)
            tk.Button(
                view_capsule,
                text=v_label,
                font=cfg.FONT["xs_b"],
                fg="#ffffff" if is_active else cfg.C("text2"),
                bg=cfg.C("accent") if is_active else cfg.C("card2"),
                activeforeground="#ffffff",
                activebackground=cfg.C("accent"),
                relief="flat",
                bd=0,
                padx=10,
                pady=3,
                cursor="hand2",
                command=lambda v=v_key: self._set_view(v),
            ).pack(side="left")

        # 2. Filter Capsule: All | Events | Tasks
        filter_capsule = tk.Frame(
            right_box,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=2,
            pady=2,
        )
        filter_capsule.pack(side="left", padx=(0, 10))

        for f_key, f_lbl in [("all", "All"), ("events", "Events"), ("tasks", "Tasks")]:
            is_active = (self._filter_type == f_key)
            tk.Button(
                filter_capsule,
                text=f_lbl,
                font=cfg.FONT["xs"],
                fg="#ffffff" if is_active else cfg.C("text2"),
                bg=cfg.C("accent") if is_active else cfg.C("card2"),
                activeforeground="#ffffff",
                activebackground=cfg.C("accent"),
                relief="flat",
                bd=0,
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda k=f_key: self._set_filter(k),
            ).pack(side="left")

        # 3. Import Button
        make_button(
            right_box,
            text="📥 Import",
            command=self._import_events,
            variant="ghost",
            font=cfg.FONT["xs_b"],
            padx=10,
            pady=4,
        ).pack(side="left", padx=(0, 6))

        # 4. Primary + New Event Button
        make_button(
            right_box,
            text="+ Event",
            command=lambda: EventDialog(
                self, self._on_add_event, default_date=self._selected_date.isoformat()
            ),
            variant="primary",
            font=cfg.FONT["xs_b"],
            padx=12,
            pady=4,
        ).pack(side="left", padx=(0, 8))

        # 5. Slide-Out Agenda Drawer Toggle
        side_active = self._show_sidebar
        side_btn = tk.Button(
            right_box,
            text="📋 Agenda Panel" if not side_active else "✕ Close Panel",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card2") if not side_active else cfg.C("card"),
            fg=cfg.C("accent") if not side_active else cfg.C("text2"),
            activebackground=cfg.C("accent"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._toggle_sidebar,
        )
        side_btn.pack(side="left")

    def _period_text(self) -> str:
        c = self._cursor
        if self._view == "month":
            return f"{MONTHS[c.month - 1]} {c.year}"
        elif self._view == "week":
            start = c - timedelta(days=(c.weekday() + 1) % 7)
            end = start + timedelta(days=6)
            return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
        elif self._view == "day":
            return c.strftime("%A, %B %d, %Y")
        else:
            return f"Schedule · {MONTHS[c.month - 1]} {c.year}"

    # ── Slide-Out Right Agenda Drawer ─────────────────────────────────────────
    def _render_sidebar(self):
        for w in self._sidebar.winfo_children():
            w.destroy()

        if not self._show_sidebar:
            self._sidebar.pack_forget()
            return
        else:
            self._sidebar.pack(side="right", fill="y", padx=(10, 0))

        # Header for the selected date
        top_hdr = tk.Frame(self._sidebar, bg=cfg.C("card"))
        top_hdr.pack(fill="x", pady=(0, 10))

        d = self._selected_date
        is_today = (d == date.today())
        d_title = d.strftime("%A, %b %d")

        tk.Label(
            top_hdr,
            text=d_title,
            font=cfg.FONT["md_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent") if is_today else cfg.C("text"),
        ).pack(anchor="w")

        items = self._items_on(d.isoformat())
        tk.Label(
            top_hdr,
            text=f"{len(items)} scheduled activities",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(2, 0))

        make_separator(self._sidebar, bg=cfg.C("border")).pack(fill="x", pady=(0, 8))

        # Scrollable items list
        scroll = ScrollableFrame(self._sidebar, bg=cfg.C("card"))
        scroll.pack(fill="both", expand=True, pady=(0, 10))
        inner = scroll.inner

        if not items:
            empty_box = tk.Frame(inner, bg=cfg.C("card"), pady=30)
            empty_box.pack(fill="x")
            tk.Label(
                empty_box,
                text="🌴\nNo activities on this date",
                font=cfg.FONT["sm"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
                justify="center",
            ).pack()
        else:
            for item in items:
                self._render_agenda_card(inner, item)

        # Quick Add Button
        make_button(
            self._sidebar,
            text=f"+ Add for {d.strftime('%b %d')}",
            command=lambda: EventDialog(
                self, self._on_add_event, default_date=d.isoformat()
            ),
            variant="primary",
            font=cfg.FONT["sm_b"],
            padx=12,
            pady=6,
        ).pack(fill="x")

    def _render_agenda_card(self, parent, item: dict):
        card = tk.Frame(
            parent,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=10,
            pady=8,
        )
        card.pack(fill="x", pady=4)

        is_task = item.get("isTask")
        accent = cfg.C("accent3") if is_task else cfg.C("accent")
        tk.Frame(card, bg=accent, width=3).place(relx=0, rely=0, relheight=1)

        # Header row
        top = tk.Frame(card, bg=cfg.C("card2"))
        top.pack(fill="x", padx=(6, 0))

        if is_task:
            prio = item.get("priority", "Medium")
            make_pill_badge(
                top, text=f"✔ TASK · {prio}", bg=cfg.C("card"), fg=cfg.C("accent3"), font_key="xs_b", padx=6, pady=1,
            ).pack(side="left")
        else:
            tm = item.get("time") or "All Day"
            rem = " 🔔" if item.get("reminder") else ""
            tk.Label(
                top, text=f"{tm}{rem}", font=cfg.FONT["xs_b"], bg=cfg.C("card2"), fg=cfg.C("accent"),
            ).pack(side="left")

        # Title
        tk.Label(
            card,
            text=item.get("title", "Untitled"),
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            wraplength=230,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=(6, 0), pady=(3, 0))

        # Description
        if item.get("description"):
            tk.Label(
                card,
                text=item["description"],
                font=cfg.FONT["xs"],
                bg=cfg.C("card2"),
                fg=cfg.C("text2"),
                wraplength=230,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=(6, 0), pady=(2, 0))

        # Action Buttons
        if not is_task:
            actions = tk.Frame(card, bg=cfg.C("card2"))
            actions.pack(anchor="w", padx=(6, 0), pady=(6, 0))

            tk.Button(
                actions, text="✏ Edit", font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("text"),
                relief="flat", bd=0, padx=6, pady=2, cursor="hand2",
                command=lambda ev=item: EventDialog(
                    self, lambda f, eid=ev["id"]: self._store.update_event(eid, **f), event=ev
                ),
            ).pack(side="left", padx=(0, 4))

            tk.Button(
                actions, text="✕ Delete", font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("danger"),
                relief="flat", bd=0, padx=6, pady=2, cursor="hand2",
                command=lambda ev=item: confirm(
                    self, f"Delete '{ev['title']}'?", lambda eid=ev["id"]: self._store.delete_event(eid)
                ),
            ).pack(side="left")

    # ── Main View Switcher ───────────────────────────────────────────────────
    def _render_view(self):
        for w in self._main_content.winfo_children():
            w.destroy()

        if self._view == "month":
            self._render_month()
        elif self._view == "week":
            self._render_week()
        elif self._view == "day":
            self._render_day()
        elif self._view == "agenda":
            self._render_agenda()

    # ── 1. Geometric Balanced Month View (Uniform Pixel-Perfect Rows) ────────
    def _render_month(self):
        container = tk.Frame(self._main_content, bg=cfg.C("bg"))
        container.pack(fill="both", expand=True)

        # ── Weekday Strip (Uniformly Aligned) ─────────────────────────────────
        weekday_bar = tk.Frame(container, bg=cfg.C("card"), height=30)
        weekday_bar.pack(fill="x", pady=(0, 2))

        for col, day in enumerate(WEEKDAYS):
            weekday_bar.columnconfigure(col, weight=1, uniform="cal_col")
            lbl = tk.Label(
                weekday_bar,
                text=day.upper(),
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card"),
                fg=cfg.C("accent") if day in ("Sun", "Sat") else cfg.C("text2"),
                anchor="center",
                pady=6,
            )
            lbl.grid(row=0, column=col, sticky="ew")

        # ── 6-Row Geometric Grid (Pixel-Perfect Uniform Sizing) ───────────────
        grid = tk.Frame(container, bg=cfg.C("bg"))
        grid.pack(fill="both", expand=True)

        for col in range(7):
            grid.columnconfigure(col, weight=1, uniform="cal_col")
        for row in range(6):
            grid.rowconfigure(row, weight=1, uniform="cal_row")

        today = date.today()
        days = _month_days(self._cursor.year, self._cursor.month)

        for idx, d in enumerate(days):
            row, col = divmod(idx, 7)
            is_today = (d == today)
            is_selected = (d == self._selected_date)
            is_cur_mon = (d.month == self._cursor.month)
            items = self._items_on(d.isoformat())

            # Subtle background difference for other-month days
            if is_cur_mon:
                cell_bg = cfg.C("card2") if is_selected else cfg.C("card")
            else:
                cell_bg = cfg.C("bg")

            # Border styling: only highlight selected or today
            if is_selected:
                border_color = cfg.C("accent")
                border_w = 2
            elif is_today:
                border_color = cfg.C("accent2")
                border_w = 1
            else:
                border_color = cfg.C("border")
                border_w = 1

            cell = tk.Frame(
                grid,
                bg=cell_bg,
                highlightthickness=border_w,
                highlightbackground=border_color,
                padx=6,
                pady=4,
                cursor="hand2",
            )
            cell.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")

            # Top Line inside Cell: Day Number (Left) + Item Count (Right)
            top_line = tk.Frame(cell, bg=cell_bg)
            top_line.pack(fill="x", pady=(0, 2))

            if is_today:
                # Beautiful circular badge for Today's number
                num_badge = tk.Label(
                    top_line,
                    text=f" {d.day} ",
                    font=cfg.FONT["xs_b"],
                    bg=cfg.C("accent"),
                    fg="#ffffff",
                )
                num_badge.pack(side="left")
            else:
                num_fg = cfg.C("text") if is_cur_mon else cfg.C("text3")
                num_lbl = tk.Label(
                    top_line,
                    text=str(d.day),
                    font=cfg.FONT["xs_b"] if is_selected else cfg.FONT["xs"],
                    bg=cell_bg,
                    fg=num_fg,
                )
                num_lbl.pack(side="left")

            if len(items) > 0 and is_cur_mon:
                count_lbl = tk.Label(
                    top_line,
                    text=f"{len(items)}",
                    font=cfg.FONT["xs"],
                    bg=cell_bg,
                    fg=cfg.C("accent") if is_today else cfg.C("text3"),
                )
                count_lbl.pack(side="right")

            # Click selection & double-click creation
            def _click_cell(target=d):
                self._selected_date = target
                self._render_header()
                self._render_sidebar()
                self._render_view()

            def _dbl_click_cell(target=d):
                EventDialog(self, self._on_add_event, default_date=target.isoformat())

            for w in (cell, top_line):
                w.bind("<Button-1>", lambda _, t=d: _click_cell(t))
                w.bind("<Double-Button-1>", lambda _, t=d: _dbl_click_cell(t))

            # Event chips container (Max 2 clean chips so rows NEVER look cluttered)
            chips_box = tk.Frame(cell, bg=cell_bg)
            chips_box.pack(fill="both", expand=True)
            chips_box.bind("<Button-1>", lambda _, t=d: _click_cell(t))
            chips_box.bind("<Double-Button-1>", lambda _, t=d: _dbl_click_cell(t))

            for item in items[:2]:
                is_task = item.get("isTask")
                chip_bg = cfg.C("card2") if cell_bg == cfg.C("card") else cfg.C("card")
                bar_color = cfg.C("accent3") if is_task else cfg.C("accent")

                chip = tk.Frame(
                    chips_box,
                    bg=chip_bg,
                    padx=4,
                    pady=2,
                    cursor="hand2",
                )
                chip.pack(fill="x", pady=1)

                # Colored left accent indicator (3px)
                tk.Frame(chip, bg=bar_color, width=3).pack(side="left", fill="y", padx=(0, 4))

                label_text = f"✔ {item.get('title')}" if is_task else f"{item.get('time', '')} {item.get('title')}".strip()
                # Clean text truncation
                truncated = label_text if len(label_text) < 19 else label_text[:17] + "…"

                lbl = tk.Label(
                    chip,
                    text=truncated,
                    font=cfg.FONT["xs"],
                    bg=chip_bg,
                    fg=cfg.C("text") if is_cur_mon else cfg.C("text2"),
                    anchor="w",
                )
                lbl.pack(side="left", fill="x", expand=True)

                def _open_event(ev_data=item):
                    if not ev_data.get("isTask"):
                        EventDialog(
                            self,
                            lambda f, eid=ev_data["id"]: self._store.update_event(eid, **f),
                            event=ev_data,
                        )

                chip.bind("<Button-1>", lambda _, ev=item: _open_event(ev))
                lbl.bind("<Button-1>", lambda _, ev=item: _open_event(ev))

            if len(items) > 2:
                more_lbl = tk.Label(
                    chips_box,
                    text=f"+{len(items)-2} more",
                    font=cfg.FONT["xs_b"],
                    bg=cell_bg,
                    fg=cfg.C("accent"),
                    anchor="w",
                    cursor="hand2",
                )
                more_lbl.pack(anchor="w", pady=(1, 0))
                more_lbl.bind("<Button-1>", lambda _, t=d: _click_cell(t))

    # ── 2. Balanced Week View ────────────────────────────────────────────────
    def _render_week(self):
        c = self._cursor
        start = c - timedelta(days=(c.weekday() + 1) % 7)
        week = [start + timedelta(days=i) for i in range(7)]
        today = date.today()

        grid = tk.Frame(self._main_content, bg=cfg.C("bg"))
        grid.pack(fill="both", expand=True)

        for col in range(7):
            grid.columnconfigure(col, weight=1, uniform="cal_col")
        grid.rowconfigure(1, weight=1)

        for col, d in enumerate(week):
            is_today = (d == today)
            is_selected = (d == self._selected_date)

            # Day Header
            hdr_bg = cfg.C("accent") if is_selected else (cfg.C("card2") if is_today else cfg.C("card"))
            hdr = tk.Frame(
                grid,
                bg=hdr_bg,
                highlightthickness=1,
                highlightbackground=cfg.C("border"),
                padx=8,
                pady=6,
                cursor="hand2",
            )
            hdr.grid(row=0, column=col, padx=2, sticky="ew")

            tk.Label(
                hdr,
                text=WEEKDAYS[col].upper(),
                font=cfg.FONT["xs_b"],
                bg=hdr_bg,
                fg="#ffffff" if is_selected else (cfg.C("accent") if is_today else cfg.C("text3")),
            ).pack()

            tk.Label(
                hdr,
                text=str(d.day),
                font=cfg.FONT["lg_b"],
                bg=hdr_bg,
                fg="#ffffff" if is_selected else (cfg.C("accent") if is_today else cfg.C("text")),
            ).pack()

            # Column Body (Scrollable day events)
            body_frame = tk.Frame(
                grid,
                bg=cfg.C("card"),
                highlightthickness=1,
                highlightbackground=cfg.C("accent") if is_selected else cfg.C("border"),
            )
            body_frame.grid(row=1, column=col, padx=2, pady=2, sticky="nsew")

            scroll = ScrollableFrame(body_frame, bg=cfg.C("card"))
            scroll.pack(fill="both", expand=True)

            items = self._items_on(d.isoformat())
            if not items:
                tk.Label(
                    scroll.inner, text="No items", font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("text3"), pady=20,
                ).pack()
            else:
                for item in items:
                    self._render_week_card(scroll.inner, item)

            def _select_day(target=d):
                self._selected_date = target
                self._render_header()
                self._render_sidebar()
                self._render_view()

            hdr.bind("<Button-1>", lambda _, t=d: _select_day(t))

    def _render_week_card(self, parent, item: dict):
        card = tk.Frame(
            parent,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=8,
            pady=6,
        )
        card.pack(fill="x", padx=4, pady=3)

        accent = cfg.C("accent3") if item.get("isTask") else cfg.C("accent")
        tk.Frame(card, bg=accent, width=3).place(relx=0, rely=0, relheight=1)

        # Time
        tm = item.get("time") or ("Task" if item.get("isTask") else "All Day")
        rem = " 🔔" if item.get("reminder") else ""
        tk.Label(
            card, text=f"{tm}{rem}", font=cfg.FONT["xs_b"], bg=cfg.C("card2"), fg=cfg.C("accent"),
        ).pack(anchor="w", padx=(6, 0))

        # Title
        tk.Label(
            card,
            text=item.get("title", ""),
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            wraplength=130,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=(6, 0), pady=(1, 0))

        if not item.get("isTask"):
            card.bind("<Button-1>", lambda _, ev=item: EventDialog(
                self, lambda f, eid=ev["id"]: self._store.update_event(eid, **f), event=ev,
            ))

    # ── 3. Focused Day View ──────────────────────────────────────────────────
    def _render_day(self):
        d = self._selected_date
        items = self._items_on(d.isoformat())

        scroll = ScrollableFrame(self._main_content, bg=cfg.C("bg"))
        scroll.pack(fill="both", expand=True)
        inner = scroll.inner

        # Day Header banner
        banner = tk.Frame(
            inner,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=20,
            pady=16,
        )
        banner.pack(fill="x", pady=(0, 12))

        tk.Label(
            banner,
            text=d.strftime("%A, %B %d, %Y"),
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(anchor="w")

        tk.Label(
            banner,
            text=f"{len(items)} scheduled activities for this day.",
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(2, 0))

        if not items:
            empty_box = tk.Frame(inner, bg=cfg.C("card"), padx=30, pady=40)
            empty_box.pack(fill="x", pady=20)
            tk.Label(
                empty_box,
                text="🌴  No events or tasks scheduled for today.",
                font=cfg.FONT["md"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
            ).pack(pady=(0, 10))

            make_button(
                empty_box,
                text="+ Schedule an Event",
                command=lambda: EventDialog(self, self._on_add_event, default_date=d.isoformat()),
                variant="primary",
            ).pack()
            return

        for item in sorted(items, key=lambda i: (i.get("time") == "", i.get("time", ""))):
            self._render_detailed_event_card(inner, item)

    def _render_detailed_event_card(self, parent, item: dict):
        card = tk.Frame(
            parent,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=18,
            pady=14,
        )
        card.pack(fill="x", pady=5)

        is_task = item.get("isTask")
        accent = cfg.C("accent3") if is_task else cfg.C("accent")
        tk.Frame(card, bg=accent, width=4).place(relx=0, rely=0, relheight=1)

        row = tk.Frame(card, bg=cfg.C("card"))
        row.pack(fill="x", padx=(8, 0))

        # Left details
        left = tk.Frame(row, bg=cfg.C("card"))
        left.pack(side="left", fill="both", expand=True)

        meta_line = tk.Frame(left, bg=cfg.C("card"))
        meta_line.pack(fill="x")

        if is_task:
            make_pill_badge(
                meta_line, text=f"✔ TASK · {item.get('priority', 'Medium')}",
                bg=cfg.C("card2"), fg=cfg.C("accent3"), font_key="xs_b", padx=6, pady=2,
            ).pack(side="left", padx=(0, 8))
        else:
            tm = item.get("time") or "All Day"
            make_pill_badge(
                meta_line, text=f"🕒 {tm}",
                bg=cfg.C("card2"), fg=cfg.C("accent"), font_key="xs_b", padx=6, pady=2,
            ).pack(side="left", padx=(0, 8))
            if item.get("reminder"):
                make_pill_badge(
                    meta_line, text="🔔 Reminder",
                    bg=cfg.C("card2"), fg=cfg.C("warn"), font_key="xs", padx=6, pady=2,
                ).pack(side="left", padx=(0, 8))

        # Title
        tk.Label(
            left,
            text=item.get("title", "Untitled"),
            font=cfg.FONT["md_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        if item.get("description"):
            tk.Label(
                left,
                text=item["description"],
                font=cfg.FONT["sm"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
                wraplength=640,
                justify="left",
                anchor="w",
            ).pack(fill="x", pady=(2, 0))

        # Right actions
        right = tk.Frame(row, bg=cfg.C("card"))
        right.pack(side="right", padx=(12, 0))

        if not is_task:
            make_button(
                right,
                text="✏ Edit",
                command=lambda ev=item: EventDialog(
                    self, lambda f, eid=ev["id"]: self._store.update_event(eid, **f), event=ev
                ),
                variant="secondary",
                font=cfg.FONT["xs_b"],
                padx=8,
                pady=4,
            ).pack(side="left", padx=2)

            make_button(
                right,
                text="✕ Delete",
                command=lambda ev=item: confirm(
                    self, f"Delete '{ev['title']}'?", lambda eid=ev["id"]: self._store.delete_event(eid)
                ),
                variant="ghost",
                font=cfg.FONT["xs_b"],
                padx=8,
                pady=4,
            ).pack(side="left")

    # ── 4. Modern Agenda / Schedule Feed View ────────────────────────────────
    def _render_agenda(self):
        scroll = ScrollableFrame(self._main_content, bg=cfg.C("bg"))
        scroll.pack(fill="both", expand=True)
        inner = scroll.inner

        today = date.today()
        all_dates = set()
        for e in self._store.events:
            if e.get("date"):
                all_dates.add(e["date"])
        for t in self._store.tasks:
            if t.get("dueDate"):
                all_dates.add(t["dueDate"])

        sorted_dates = sorted([d for d in all_dates if d >= today.isoformat()])

        if not sorted_dates:
            empty = tk.Frame(inner, bg=cfg.C("card"), padx=30, pady=40)
            empty.pack(fill="x", pady=20)
            tk.Label(
                empty,
                text="📋  No upcoming events or scheduled tasks found.",
                font=cfg.FONT["md"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
            ).pack(pady=(0, 10))
            make_button(
                empty,
                text="+ Create New Event",
                command=lambda: EventDialog(self, self._on_add_event),
                variant="primary",
            ).pack()
            return

        for date_str in sorted_dates:
            items = self._items_on(date_str)
            if not items:
                continue

            d_obj = date.fromisoformat(date_str)
            if d_obj == today:
                header_title = f"Today · {d_obj.strftime('%A, %b %d')}"
                header_color = cfg.C("accent")
            elif d_obj == today + timedelta(days=1):
                header_title = f"Tomorrow · {d_obj.strftime('%A, %b %d')}"
                header_color = cfg.C("accent2")
            else:
                header_title = d_obj.strftime("%A, %B %d, %Y")
                header_color = cfg.C("text")

            group_hdr = tk.Frame(inner, bg=cfg.C("bg"))
            group_hdr.pack(fill="x", pady=(12, 4))

            tk.Label(
                group_hdr,
                text=header_title,
                font=cfg.FONT["md_b"],
                bg=cfg.C("bg"),
                fg=header_color,
            ).pack(side="left")

            make_pill_badge(
                group_hdr,
                text=f"{len(items)} items",
                bg=cfg.C("card2"),
                fg=cfg.C("text3"),
                font_key="xs",
                padx=6,
                pady=1,
            ).pack(side="left", padx=10)

            for item in items:
                self._render_detailed_event_card(inner, item)

    # ── Helpers & State Controllers ──────────────────────────────────────────
    def _items_on(self, date_str: str) -> list:
        f_type = getattr(self, "_filter_type", "all")
        items = []

        # Events
        if f_type in ("all", "events"):
            for e in self._store.events:
                if e.get("date") == date_str:
                    items.append(dict(e, isTask=False))

        # Tasks
        if f_type in ("all", "tasks"):
            for t in self._store.tasks:
                if t.get("dueDate") == date_str:
                    items.append({
                        "id": f"task-{t['id']}",
                        "raw_id": t["id"],
                        "title": t["title"],
                        "date": t.get("dueDate"),
                        "time": "",
                        "isTask": True,
                        "priority": t.get("priority", "Medium"),
                        "status": t.get("status", "Todo"),
                        "category": t.get("category", "General"),
                        "description": t.get("description", ""),
                    })

        return sorted(items, key=lambda i: (i.get("time") == "", i.get("time", "")))

    def _on_add_event(self, fields):
        self._store.add_event(**fields)

    def _set_filter(self, f_key: str):
        self._filter_type = f_key
        self._render_header()
        self._render_sidebar()
        self._render_view()

    def _set_view(self, v: str):
        self._view = v
        self._render_header()
        self._render_view()

    def _toggle_sidebar(self):
        self._show_sidebar = not self._show_sidebar
        self._render_header()
        self._render_sidebar()

    def _prev(self):
        if self._view == "month":
            self._prev_month()
        elif self._view == "week":
            self._cursor -= timedelta(weeks=1)
            self._refresh()
        else:
            self._cursor -= timedelta(days=1)
            self._selected_date = self._cursor
            self._refresh()

    def _next(self):
        if self._view == "month":
            self._next_month()
        elif self._view == "week":
            self._cursor += timedelta(weeks=1)
            self._refresh()
        else:
            self._cursor += timedelta(days=1)
            self._selected_date = self._cursor
            self._refresh()

    def _prev_month(self):
        m = self._cursor.month - 1
        y = self._cursor.year
        if m == 0:
            m, y = 12, y - 1
        self._cursor = self._cursor.replace(year=y, month=m, day=1)
        self._refresh()

    def _next_month(self):
        m = self._cursor.month + 1
        y = self._cursor.year
        if m == 13:
            m, y = 1, y + 1
        self._cursor = self._cursor.replace(year=y, month=m, day=1)
        self._refresh()

    def _today(self):
        self._cursor = date.today()
        self._selected_date = date.today()
        self._refresh()

    def _refresh(self):
        self._render_header()
        self._render_sidebar()
        self._render_view()

    def _import_events(self):
        filetypes = [
            ("Supported Calendar Files", "*.ics;*.json;*.csv"),
            ("iCalendar files", "*.ics"),
            ("JSON files", "*.json"),
            ("CSV files", "*.csv"),
            ("All files", "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            title="Import Calendar Activities & Events",
            filetypes=filetypes,
        )
        if not paths:
            return

        total_imported = 0
        errors = []
        for path in paths:
            try:
                events = parse_events_file(path)
                count = self._store.import_events(events)
                total_imported += count
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        if total_imported > 0:
            msg = f"Successfully imported {total_imported} event/activit{'ies' if total_imported != 1 else 'y'} into OneDesk!"
            if errors:
                msg += "\n\nWarnings/Errors:\n" + "\n".join(errors)
            messagebox.showinfo("Events Imported", msg)
        else:
            err_msg = "No valid calendar activities found to import."
            if errors:
                err_msg += "\n\nDetails:\n" + "\n".join(errors)
            messagebox.showwarning("Import Events", err_msg)
