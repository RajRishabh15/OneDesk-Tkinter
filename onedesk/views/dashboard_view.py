"""
OneDesk Dashboard View - dashboard_view.py
Modern, fluid at-a-glance productivity dashboard:
- User profile avatar with instant greeting and contextual time subtitle
- Interactive quick-add task bar
- 6-metric overview strip with fluid round icon bubbles and progress tracking
- 3-column workspace: Pending Tasks (with tick & delete buttons), Today's Schedule, Recent Notes
"""

import tkinter as tk
import time
from datetime import date
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_separator, ScrollableFrame, Tooltip,
    create_circular_avatar, RoundIconButton, make_pill_badge,
)
from ..components.modals import TaskDialog, EventDialog, NoteDialog


class DashboardView(tk.Frame):
    def __init__(self, parent, store, auth, on_navigate=None, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store = store
        self._auth  = auth
        self._on_navigate = on_navigate
        self._avatar_img = None
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
        if not self.winfo_exists():
            return
        for w in self._container.winfo_children():
            w.destroy()
        self._render()

    @staticmethod
    def _time_label():
        h = time.localtime().tm_hour
        if h < 12:
            return "Morning Focus"
        if h < 17:
            return "Afternoon Momentum"
        return "Evening Wrap-up"

    def _card(self, parent, **kw):
        kw.setdefault("bg", cfg.C("card"))
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", cfg.C("border"))
        return tk.Frame(parent, **kw)

    def _render(self):
        P     = 18
        store = self._store
        today = date.today()

        # ── 1. Fluid Hero Greeting Banner ───────────────────────────────────
        banner_card = self._card(self._container, padx=22, pady=18)
        banner_card.pack(fill="x", padx=P, pady=(P, 12))

        # Left Cluster: User Circular Avatar + Name Greeting
        left_b = tk.Frame(banner_card, bg=cfg.C("card"))
        left_b.pack(side="left", fill="y")

        # Avatar Preview with rounded ring
        name = self._auth.display_name or "there"
        initials = "".join(p[0].upper() for p in name.split()[:2]) or "U"
        av_path = getattr(self._auth, "avatar_path", "")

        self._avatar_img = create_circular_avatar(
            image_path=av_path,
            size=52,
            text=initials,
            bg=cfg.C("accent"),
        )
        av_btn = tk.Label(
            left_b,
            image=self._avatar_img,
            bg=cfg.C("card"),
            cursor="hand2" if self._on_navigate else "arrow",
            bd=0,
        )
        av_btn.pack(side="left", padx=(0, 16))
        if self._on_navigate:
            av_btn.bind("<Button-1>", lambda _: self._on_navigate("Settings"))
            Tooltip(av_btn, "Edit profile picture in Settings")

        # Text greetings
        greet_box = tk.Frame(left_b, bg=cfg.C("card"))
        greet_box.pack(side="left", fill="y", anchor="center")

        tk.Label(
            greet_box,
            text=f"Welcome back, {name} 👋",
            font=cfg.FONT["2xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            anchor="w",
        ).pack(anchor="w")

        date_str = today.strftime("%A, %B %d")
        tk.Label(
            greet_box,
            text=f"✦  {date_str}  •  {self._time_label()}",
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        # Right Cluster: Fluid Quick-Add Input + Buttons
        right_b = tk.Frame(banner_card, bg=cfg.C("card"))
        right_b.pack(side="right", anchor="center")

        self._inline_var = tk.StringVar()
        _PH = "Quick-add a task…"

        qa_wrap = tk.Frame(
            right_b,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=2,
            pady=2,
        )
        qa_wrap.pack(side="left", padx=(0, 10))

        qa_entry = tk.Entry(
            qa_wrap,
            textvariable=self._inline_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            width=26,
        )
        qa_entry.pack(padx=10, pady=6)
        qa_entry.insert(0, _PH)

        def _fi(_):
            if qa_entry.get() == _PH:
                qa_entry.delete(0, "end")
                qa_entry.configure(fg=cfg.C("text"))
            qa_wrap.configure(highlightbackground=cfg.C("accent"))

        def _fo(_):
            if not qa_entry.get():
                qa_entry.insert(0, _PH)
                qa_entry.configure(fg=cfg.C("text3"))
            qa_wrap.configure(highlightbackground=cfg.C("border"))

        qa_entry.bind("<FocusIn>",  _fi)
        qa_entry.bind("<FocusOut>", _fo)
        qa_entry.bind("<Return>",   self._quick_add)

        # Fluid Add button with round styling
        RoundIconButton(
            right_b,
            icon="＋",
            command=self._quick_add,
            size=32,
            bg_color=cfg.C("accent"),
            fg_color="#ffffff",
            hover_bg=cfg.C("accent2"),
            hover_fg="#ffffff",
            border_color=cfg.C("accent"),
            tooltip="Quick Add Task",
            parent_bg=cfg.C("card"),
        ).pack(side="left", padx=(0, 8))

        make_button(
            right_b,
            text="+ Full Task",
            command=lambda: TaskDialog(self, self._on_add_task),
            variant="secondary",
            font=cfg.FONT["xs_b"],
            padx=12,
            pady=6,
        ).pack(side="left")

        # ── 2. Fluid 6-Metric Stat Strip ────────────────────────────────────
        total     = len(store.tasks)
        completed = len(store.completed_tasks)
        pending   = len(store.pending_tasks)
        pct       = store.completion_pct

        strip = tk.Frame(self._container, bg=cfg.C("bg"))
        strip.pack(fill="x", padx=P, pady=(0, 14))

        stat_defs = [
            ("📋", "Tasks",   str(total),                cfg.C("accent"),  "Tasks"),
            ("✓",  "Done",    str(completed),            cfg.C("success"), "Tasks"),
            ("⏳",  "Pending", str(pending),              cfg.C("warn"),    "Tasks"),
            ("📝", "Notes",   str(len(store.notes)),     cfg.C("accent2"), "Notes"),
            ("🗓",  "Today",   str(len(store.today_events)), cfg.C("accent3"), "Calendar"),
        ]

        for i, (icon, label, value, color, target_view) in enumerate(stat_defs):
            sc = self._card(strip, padx=14, pady=12)
            sc.grid(row=0, column=i, padx=(0, 8), sticky="nsew")
            strip.columnconfigure(i, weight=1)

            # Header row with fluid icon bubble
            hdr = tk.Frame(sc, bg=cfg.C("card"))
            hdr.pack(fill="x")

            # Round Icon Bubble
            icon_bubble = tk.Label(
                hdr,
                text=icon,
                font=cfg.FONT["sm_b"],
                bg=cfg.C("card2"),
                fg=color,
                padx=6,
                pady=2,
            )
            icon_bubble.pack(side="left")

            tk.Label(
                hdr,
                text=label.upper(),
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
            ).pack(side="right", anchor="e")

            tk.Label(
                sc,
                text=value,
                font=cfg.FONT["2xl_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text"),
                anchor="w",
            ).pack(anchor="w", pady=(6, 0))

            # Hover feedback and optional navigation click
            if self._on_navigate and target_view:
                def _nav(tv=target_view):
                    self._on_navigate(tv)

                for w in (sc, hdr, icon_bubble):
                    w.configure(cursor="hand2")
                    w.bind("<Button-1>", lambda _, fn=_nav: fn())

                def _sc_enter(e, card=sc, ic=icon_bubble):
                    card.configure(bg=cfg.C("card2"), highlightbackground=cfg.C("accent"))
                def _sc_leave(e, card=sc, ic=icon_bubble):
                    card.configure(bg=cfg.C("card"), highlightbackground=cfg.C("border"))

                sc.bind("<Enter>", _sc_enter)
                sc.bind("<Leave>", _sc_leave)

        # 6th Card: Completion Rate Meter
        pc = self._card(strip, padx=14, pady=12)
        pc.grid(row=0, column=5, sticky="nsew")
        strip.columnconfigure(5, weight=1)

        p_hdr = tk.Frame(pc, bg=cfg.C("card"))
        p_hdr.pack(fill="x")

        p_bubble = tk.Label(
            p_hdr,
            text="🎯",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("accent"),
            padx=6,
            pady=2,
        )
        p_bubble.pack(side="left")

        tk.Label(
            p_hdr,
            text="COMPLETION",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(side="right", anchor="e")

        tk.Label(
            pc,
            text=f"{pct}%",
            font=cfg.FONT["2xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
            anchor="w",
        ).pack(anchor="w", pady=(6, 8))

        bar_bg = tk.Frame(pc, bg=cfg.C("card2"), height=6, highlightthickness=0)
        bar_bg.pack(fill="x")
        fill_w = max(0.0, min(1.0, pct / 100.0)) if pct else 0.0
        tk.Frame(bar_bg, bg=cfg.C("accent"), height=6).place(
            x=0, y=0, relwidth=fill_w, height=6
        )

        # ── 3. Three-Column Workspace Section ───────────────────────────────
        lower = tk.Frame(self._container, bg=cfg.C("bg"))
        lower.pack(fill="both", expand=True, padx=P, pady=(0, P))
        lower.columnconfigure(0, weight=5)
        lower.columnconfigure(1, weight=3)
        lower.columnconfigure(2, weight=4)

        # =====================================================================
        # COLUMN 0: Pending Tasks (with Tick & Delete Round Buttons)
        # =====================================================================
        tc = self._card(lower)
        tc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        t_header = tk.Frame(tc, bg=cfg.C("card"), padx=16, pady=12)
        t_header.pack(fill="x")

        tk.Label(
            t_header,
            text="Pending Tasks",
            font=cfg.FONT["md_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(side="left")

        make_pill_badge(
            t_header,
            text=f"{pending} active",
            bg=cfg.C("card2"),
            fg=cfg.C("accent"),
            font_key="xs_b",
        ).pack(side="left", padx=8)

        if self._on_navigate:
            tk.Button(
                t_header,
                text="View All →",
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
                activeforeground=cfg.C("accent"),
                activebackground=cfg.C("card"),
                relief="flat",
                bd=0,
                cursor="hand2",
                command=lambda: self._on_navigate("Tasks"),
            ).pack(side="right")

        make_separator(tc, bg=cfg.C("border")).pack(fill="x", padx=16)

        pending_tasks = store.pending_tasks[:6]
        if pending_tasks:
            t_list = tk.Frame(tc, bg=cfg.C("card"), padx=12, pady=6)
            t_list.pack(fill="both", expand=True)

            for t in pending_tasks:
                trow = tk.Frame(
                    t_list,
                    bg=cfg.C("card"),
                    padx=8,
                    pady=6,
                    highlightthickness=1,
                    highlightbackground=cfg.C("card"),
                )
                trow.pack(fill="x", pady=2)

                # Priority Pill Badge
                prio = t.get("priority", "Medium")
                prio_fg = cfg.PRIORITY_FG.get(prio, cfg.C("text2"))
                prio_bg = cfg.PRIORITY_BG.get(prio, cfg.C("card2"))
                make_pill_badge(
                    trow,
                    text=prio.upper()[:3],
                    bg=prio_bg,
                    fg=prio_fg,
                    font_key="xs_b",
                    padx=6,
                    pady=2,
                ).pack(side="left", padx=(0, 8))

                # Task Title & Metadata
                info_box = tk.Frame(trow, bg=cfg.C("card"))
                info_box.pack(side="left", fill="both", expand=True)

                title_lbl = tk.Label(
                    info_box,
                    text=t.get("title", ""),
                    font=cfg.FONT["sm_b"],
                    bg=cfg.C("card"),
                    fg=cfg.C("text"),
                    anchor="w",
                )
                title_lbl.pack(fill="x")

                sub_parts = []
                cat = t.get("category", "")
                if cat:
                    sub_parts.append(cat)
                due = t.get("dueDate", "")
                if due:
                    sub_parts.append(f"Due {due}")

                if sub_parts:
                    tk.Label(
                        info_box,
                        text="  •  ".join(sub_parts),
                        font=cfg.FONT["xs"],
                        bg=cfg.C("card"),
                        fg=cfg.C("text3"),
                        anchor="w",
                    ).pack(fill="x")

                # Action Container on Right: Tick Box AND Delete Button!
                act_box = tk.Frame(trow, bg=cfg.C("card"))
                act_box.pack(side="right", padx=(6, 0))

                # 1. Round Tick Button (Complete)
                def _do_complete(tid=t["id"]):
                    store.toggle_complete(tid)

                RoundIconButton(
                    act_box,
                    icon="✓",
                    command=_do_complete,
                    size=26,
                    bg_color=cfg.C("card2"),
                    fg_color=cfg.C("text3"),
                    hover_bg=cfg.C("success"),
                    hover_fg="#ffffff",
                    border_color=cfg.C("border"),
                    tooltip="Mark Complete",
                    parent_bg=cfg.C("card"),
                ).pack(side="left", padx=(0, 4))

                # 2. Round Delete Button (Beside the Tick Box!)
                def _do_delete(tid=t["id"]):
                    store.delete_task(tid)

                RoundIconButton(
                    act_box,
                    icon="✕",
                    command=_do_delete,
                    size=26,
                    bg_color=cfg.C("card2"),
                    fg_color=cfg.C("text3"),
                    hover_bg=cfg.C("danger"),
                    hover_fg="#ffffff",
                    border_color=cfg.C("border"),
                    tooltip="Delete Task",
                    parent_bg=cfg.C("card"),
                ).pack(side="left")

                # Row Hover effect
                def _row_hover(e, r=trow, ib=info_box, ab=act_box, tl=title_lbl, entering=True):
                    bg_col = cfg.C("card2") if entering else cfg.C("card")
                    border_col = cfg.C("border") if entering else cfg.C("card")
                    r.configure(bg=bg_col, highlightbackground=border_col)
                    ib.configure(bg=bg_col)
                    ab.configure(bg=bg_col)
                    tl.configure(bg=bg_col)

                trow.bind("<Enter>", lambda e, r=trow, ib=info_box, ab=act_box, tl=title_lbl: _row_hover(e, r, ib, ab, tl, True))
                trow.bind("<Leave>", lambda e, r=trow, ib=info_box, ab=act_box, tl=title_lbl: _row_hover(e, r, ib, ab, tl, False))
        else:
            empty_box = tk.Frame(tc, bg=cfg.C("card"), padx=16, pady=28)
            empty_box.pack(fill="both", expand=True)

            tk.Label(
                empty_box,
                text="🎉",
                font=(cfg.FONT_FAMILY, 24),
                bg=cfg.C("card"),
            ).pack()

            tk.Label(
                empty_box,
                text="All caught up!",
                font=cfg.FONT["sm_b"],
                bg=cfg.C("card"),
                fg=cfg.C("success"),
            ).pack(pady=(4, 2))

            tk.Label(
                empty_box,
                text="No pending tasks right now. Great job!",
                font=cfg.FONT["xs"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
            ).pack()

        # =====================================================================
        # COLUMN 1: Today's Schedule (Events)
        # =====================================================================
        ec = self._card(lower)
        ec.grid(row=0, column=1, sticky="nsew", padx=4)

        e_header = tk.Frame(ec, bg=cfg.C("card"), padx=16, pady=12)
        e_header.pack(fill="x")

        tk.Label(
            e_header,
            text="Today's Events",
            font=cfg.FONT["md_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(side="left")

        ev_count = len(store.today_events)
        make_pill_badge(
            e_header,
            text=f"{ev_count}",
            bg=cfg.C("card2"),
            fg=cfg.C("accent2"),
            font_key="xs_b",
        ).pack(side="left", padx=8)

        if self._on_navigate:
            tk.Button(
                e_header,
                text="Calendar →",
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
                activeforeground=cfg.C("accent"),
                activebackground=cfg.C("card"),
                relief="flat",
                bd=0,
                cursor="hand2",
                command=lambda: self._on_navigate("Calendar"),
            ).pack(side="right")

        make_separator(ec, bg=cfg.C("border")).pack(fill="x", padx=16)

        if store.today_events:
            e_list = tk.Frame(ec, bg=cfg.C("card"), padx=12, pady=6)
            e_list.pack(fill="both", expand=True)

            for ev in store.today_events:
                erow = tk.Frame(
                    e_list,
                    bg=cfg.C("card2"),
                    padx=10,
                    pady=8,
                    highlightthickness=1,
                    highlightbackground=cfg.C("border"),
                )
                erow.pack(fill="x", pady=3)

                time_txt = ev.get("time", "All day")
                make_pill_badge(
                    erow,
                    text=time_txt,
                    bg=cfg.C("accent2"),
                    fg="#ffffff",
                    font_key="xs_b",
                    padx=6,
                    pady=2,
                ).pack(side="left", padx=(0, 8))

                ev_info = tk.Frame(erow, bg=cfg.C("card2"))
                ev_info.pack(side="left", fill="both", expand=True)

                tk.Label(
                    ev_info,
                    text=ev.get("title", ""),
                    font=cfg.FONT["sm_b"],
                    bg=cfg.C("card2"),
                    fg=cfg.C("text"),
                    anchor="w",
                ).pack(fill="x")

                desc = ev.get("description", "")
                if desc:
                    tk.Label(
                        ev_info,
                        text=desc[:45],
                        font=cfg.FONT["xs"],
                        bg=cfg.C("card2"),
                        fg=cfg.C("text3"),
                        anchor="w",
                    ).pack(fill="x")

                if ev.get("reminder"):
                    tk.Label(
                        erow,
                        text="🔔",
                        font=cfg.FONT["xs"],
                        bg=cfg.C("card2"),
                    ).pack(side="right")
        else:
            empty_e = tk.Frame(ec, bg=cfg.C("card"), padx=16, pady=28)
            empty_e.pack(fill="both", expand=True)

            tk.Label(
                empty_e,
                text="🗓",
                font=(cfg.FONT_FAMILY, 24),
                bg=cfg.C("card"),
            ).pack()

            tk.Label(
                empty_e,
                text="No events scheduled",
                font=cfg.FONT["sm_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
            ).pack(pady=(4, 2))

            tk.Label(
                empty_e,
                text="Your calendar is free for today.",
                font=cfg.FONT["xs"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
            ).pack()

            make_button(
                empty_e,
                text="+ New Event",
                command=lambda: EventDialog(self, lambda f: self._store.add_event(**f)),
                variant="ghost",
                font=cfg.FONT["xs_b"],
                padx=10,
                pady=4,
            ).pack(pady=(12, 0))

        # =====================================================================
        # COLUMN 2: Recent Notes (Interactive Chips)
        # =====================================================================
        nc = self._card(lower)
        nc.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        n_header = tk.Frame(nc, bg=cfg.C("card"), padx=16, pady=12)
        n_header.pack(fill="x")

        tk.Label(
            n_header,
            text="Recent Notes",
            font=cfg.FONT["md_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(side="left")

        make_pill_badge(
            n_header,
            text=f"{len(store.notes)} total",
            bg=cfg.C("card2"),
            fg=cfg.C("accent2"),
            font_key="xs_b",
        ).pack(side="left", padx=8)

        if self._on_navigate:
            tk.Button(
                n_header,
                text="Notes →",
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
                activeforeground=cfg.C("accent"),
                activebackground=cfg.C("card"),
                relief="flat",
                bd=0,
                cursor="hand2",
                command=lambda: self._on_navigate("Notes"),
            ).pack(side="right")

        make_separator(nc, bg=cfg.C("border")).pack(fill="x", padx=16)

        recent = sorted(
            store.notes,
            key=lambda n: (n.get("pinned", False), n.get("createdAt", "")),
            reverse=True,
        )[:4]

        if recent:
            npad = tk.Frame(nc, bg=cfg.C("card"), padx=12, pady=6)
            npad.pack(fill="both", expand=True)

            for note in recent:
                fg_c, bg_c = cfg.color_pair(note.get("color", "violet"))
                chip = tk.Frame(
                    npad,
                    bg=bg_c,
                    padx=10,
                    pady=8,
                    highlightthickness=1,
                    highlightbackground=fg_c,
                    cursor="hand2" if self._on_navigate else "arrow",
                )
                chip.pack(fill="x", pady=3)

                chip_top = tk.Frame(chip, bg=bg_c)
                chip_top.pack(fill="x")

                if note.get("pinned"):
                    tk.Label(
                        chip_top,
                        text="📌",
                        font=cfg.FONT["xs"],
                        bg=bg_c,
                    ).pack(side="left", padx=(0, 4))

                tk.Label(
                    chip_top,
                    text=note.get("title", "Untitled Note"),
                    font=cfg.FONT["sm_b"],
                    bg=bg_c,
                    fg=fg_c,
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                cat_txt = note.get("category", "")
                if cat_txt:
                    make_pill_badge(
                        chip_top,
                        text=cat_txt,
                        bg=bg_c,
                        fg=fg_c,
                        font_key="xs",
                        padx=4,
                        pady=1,
                    ).pack(side="right")

                body = note.get("description", "").strip()[:50]
                if body:
                    tk.Label(
                        chip,
                        text=body,
                        font=cfg.FONT["xs"],
                        bg=bg_c,
                        fg=fg_c,
                        anchor="w",
                        wraplength=210,
                        justify="left",
                    ).pack(anchor="w", pady=(3, 0))

                if self._on_navigate:
                    chip.bind("<Button-1>", lambda _, n=note: self._on_navigate("Notes"))
        else:
            empty_n = tk.Frame(nc, bg=cfg.C("card"), padx=16, pady=28)
            empty_n.pack(fill="both", expand=True)

            tk.Label(
                empty_n,
                text="📝",
                font=(cfg.FONT_FAMILY, 24),
                bg=cfg.C("card"),
            ).pack()

            tk.Label(
                empty_n,
                text="No notes yet",
                font=cfg.FONT["sm_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
            ).pack(pady=(4, 2))

            tk.Label(
                empty_n,
                text="Capture your thoughts, ideas, and drafts.",
                font=cfg.FONT["xs"],
                bg=cfg.C("card"),
                fg=cfg.C("text3"),
            ).pack()

            make_button(
                empty_n,
                text="+ New Note",
                command=lambda: NoteDialog(self, lambda f: self._store.add_note(**f)),
                variant="ghost",
                font=cfg.FONT["xs_b"],
                padx=10,
                pady=4,
            ).pack(pady=(12, 0))

    # ── Actions ──────────────────────────────────────────────────────────────
    def _quick_add(self, _event=None):
        text = self._inline_var.get().strip()
        ph = "Quick-add a task"
        if not text or text.startswith(ph):
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
