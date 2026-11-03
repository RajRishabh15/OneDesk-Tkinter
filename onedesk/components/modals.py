"""
OneDesk Modals — modals.py
Reusable Toplevel dialogs for Notes, Tasks, Events, and Confirmations.
Styled for Windows native dark/light modes with pinned action bars and responsive layouts.
"""

import calendar
from datetime import date, datetime, timedelta
import tkinter as tk
from .. import config as cfg
from ..platform_helpers import apply_window_theme, center_window
from ..time_utils import format_time_12h
from .ui_helpers import make_button, make_entry, make_text


def _modal_window(parent, title, width=520, height=520):
    """Create, center, and style a modal Toplevel."""
    top = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
    win = tk.Toplevel(top)
    win.title(title)
    win.configure(bg=cfg.C("card"))
    win.minsize(width - 40, height - 40)

    # Center over top-level parent window
    center_window(win, width, height, parent=top)

    # Windows dark/light title bar integration
    apply_window_theme(win, dark=(cfg.current_theme_name() == "dark"))

    # Make modal and bind Escape to close
    win.transient(top)
    win.lift()
    win.focus_force()
    win.bind("<Escape>", lambda _: win.destroy())
    win.grab_set()

    return win


def _labeled_entry(parent, label_text: str, textvariable: tk.StringVar, placeholder: str = "") -> tk.Entry:
    """Pack a (Label, Entry) pair as a horizontal row with proper parent-child hierarchy."""
    row = tk.Frame(parent, bg=cfg.C("card"))
    row.pack(fill="x", pady=(0, 10))
    tk.Label(
        row,
        text=label_text,
        font=cfg.FONT["xs_b"],
        bg=cfg.C("card"),
        fg=cfg.C("text2"),
        width=13,
        anchor="w",
    ).pack(side="left")
    entry = make_entry(row, textvariable=textvariable, width=28, placeholder=placeholder)
    entry.pack(side="left", fill="x", expand=True)
    return entry


def _labeled_date_entry(parent, label_text: str, textvariable: tk.StringVar) -> tk.Entry:
    """Pack a date entry with a modern, fully-responsive popup calendar button."""
    row = tk.Frame(parent, bg=cfg.C("card"))
    row.pack(fill="x", pady=(0, 10))
    tk.Label(
        row,
        text=label_text,
        font=cfg.FONT["xs_b"],
        bg=cfg.C("card"),
        fg=cfg.C("text2"),
        width=13,
        anchor="w",
    ).pack(side="left")
    entry = make_entry(row, textvariable=textvariable, width=24)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def _open_calendar():
        raw_val = textvariable.get().strip()
        selected_date = None
        if raw_val:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    selected_date = datetime.strptime(raw_val, fmt).date()
                    break
                except ValueError:
                    pass
            if not selected_date:
                try:
                    selected_date = date.fromisoformat(raw_val)
                except ValueError:
                    pass

        today = date.today()
        if not selected_date:
            selected_date = today

        month_state = {"year": selected_date.year, "month": selected_date.month}
        focused_date = {"date": selected_date}

        picker = tk.Toplevel(parent.winfo_toplevel())
        picker.title("Select Date")
        picker.configure(bg=cfg.C("card"))
        apply_window_theme(picker, dark=(cfg.current_theme_name() == "dark"))
        picker.transient(parent.winfo_toplevel())

        # Responsive base dimensions and minimum size
        picker_w = 350
        picker_h = 410
        picker.minsize(320, 370)
        picker.resizable(True, True)

        # Smart screen-bounded positioning:
        picker.update_idletasks()
        screen_w = picker.winfo_screenwidth()
        screen_h = picker.winfo_screenheight()

        btn_x = calendar_btn.winfo_rootx()
        btn_y = calendar_btn.winfo_rooty()
        btn_h = calendar_btn.winfo_height()

        # Clamp horizontal position within screen bounds
        pos_x = btn_x
        if pos_x + picker_w > screen_w - 16:
            pos_x = screen_w - picker_w - 16
        if pos_x < 10:
            pos_x = 10

        # Vertical placement: flip above button if near screen bottom
        pos_y = btn_y + btn_h + 4
        if pos_y + picker_h > screen_h - 50:
            above_y = btn_y - picker_h - 4
            if above_y >= 10:
                pos_y = above_y
            else:
                pos_y = max(10, screen_h - picker_h - 50)

        picker.geometry(f"{picker_w}x{picker_h}+{pos_x}+{pos_y}")

        def _close():
            if picker.winfo_exists():
                picker.destroy()
            try:
                parent.winfo_toplevel().grab_set()
            except tk.TclError:
                pass

        def _choose(target_date: date):
            textvariable.set(target_date.isoformat())
            _close()

        def _select_today():
            _choose(date.today())

        def _clear_date():
            textvariable.set("")
            _close()

        # Container hierarchy
        header = tk.Frame(picker, bg=cfg.C("card"))
        header.pack(fill="x", padx=12, pady=(10, 6))

        grid = tk.Frame(picker, bg=cfg.C("card"))
        grid.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        footer = tk.Frame(picker, bg=cfg.C("card"))
        footer.pack(fill="x", padx=12, pady=(0, 10))

        # Footer action buttons
        make_button(footer, "Today", command=_select_today, variant="secondary", font=cfg.FONT["xs_b"], padx=10, pady=3).pack(side="left")
        make_button(footer, "Clear", command=_clear_date, variant="ghost", font=cfg.FONT["xs_b"], padx=10, pady=3).pack(side="left", padx=6)
        make_button(footer, "Cancel", command=_close, variant="ghost", font=cfg.FONT["xs_b"], padx=10, pady=3).pack(side="right")

        def _shift_month(amount: int):
            year, month = month_state["year"], month_state["month"] + amount
            if month < 1:
                year, month = year - 1, 12
            elif month > 12:
                year, month = year + 1, 1
            month_state.update(year=year, month=month)
            _render()

        def _shift_year(amount: int):
            month_state["year"] += amount
            _render()

        def _render():
            for child in header.winfo_children():
                child.destroy()
            for child in grid.winfo_children():
                child.destroy()

            # ── Header Navigation ──
            nav_left = tk.Frame(header, bg=cfg.C("card"))
            nav_left.pack(side="left")
            make_button(nav_left, "«", command=lambda: _shift_year(-1), variant="ghost", font=cfg.FONT["xs_b"], padx=6, pady=2).pack(side="left", padx=(0, 2))
            make_button(nav_left, "‹", command=lambda: _shift_month(-1), variant="ghost", font=cfg.FONT["xs_b"], padx=6, pady=2).pack(side="left")

            month_title = f"{calendar.month_name[month_state['month']]}  {month_state['year']}"
            title_lbl = tk.Label(
                header,
                text=month_title,
                font=cfg.FONT["md_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text"),
                anchor="center",
            )
            title_lbl.pack(side="left", expand=True, fill="x")

            nav_right = tk.Frame(header, bg=cfg.C("card"))
            nav_right.pack(side="right")
            make_button(nav_right, "›", command=lambda: _shift_month(1), variant="ghost", font=cfg.FONT["xs_b"], padx=6, pady=2).pack(side="left", padx=(0, 2))
            make_button(nav_right, "»", command=lambda: _shift_year(1), variant="ghost", font=cfg.FONT["xs_b"], padx=6, pady=2).pack(side="left")

            # ── Grid Configuration: 7 uniform columns and 6 uniform week rows ──
            for c in range(7):
                grid.grid_columnconfigure(c, weight=1, uniform="cal_col")
            grid.grid_rowconfigure(0, weight=0)
            for r in range(1, 7):
                grid.grid_rowconfigure(r, weight=1, uniform="cal_row")

            # Weekday header labels
            weekdays = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
            for col, wd in enumerate(weekdays):
                is_weekend = col in (5, 6)
                wd_fg = cfg.C("accent3") if is_weekend else cfg.C("text2")
                tk.Label(
                    grid,
                    text=wd,
                    font=cfg.FONT["xs_b"],
                    bg=cfg.C("card"),
                    fg=wd_fg,
                    anchor="center",
                ).grid(row=0, column=col, pady=(2, 6), sticky="nsew")

            # Generate full 6 weeks (42 dates) for complete month visibility and stable layout
            cal = calendar.Calendar(firstweekday=calendar.MONDAY)
            weeks = cal.monthdatescalendar(month_state["year"], month_state["month"])
            while len(weeks) < 6:
                last_d = weeks[-1][-1]
                weeks.append([last_d + timedelta(days=i) for i in range(1, 8)])

            for row_idx, week in enumerate(weeks, start=1):
                for col_idx, d in enumerate(week):
                    is_cur_month = (d.month == month_state["month"])
                    is_sel = (d == focused_date["date"])
                    is_tod = (d == today)

                    if is_sel:
                        btn_bg = cfg.C("accent")
                        btn_fg = "#ffffff"
                        btn_ab = cfg.C("accent2")
                        btn_font = cfg.FONT["sm_b"]
                        btn_relief = "flat"
                        btn_bd = 0
                    elif is_tod:
                        btn_bg = cfg.C("card2")
                        btn_fg = cfg.C("accent")
                        btn_ab = cfg.C("border")
                        btn_font = cfg.FONT["sm_b"]
                        btn_relief = "solid"
                        btn_bd = 1
                    elif is_cur_month:
                        btn_bg = cfg.C("card2")
                        btn_fg = cfg.C("text")
                        btn_ab = cfg.C("border")
                        btn_font = cfg.FONT["sm"]
                        btn_relief = "flat"
                        btn_bd = 0
                    else:
                        btn_bg = cfg.C("card")
                        btn_fg = cfg.C("text3")
                        btn_ab = cfg.C("card2")
                        btn_font = cfg.FONT["xs"]
                        btn_relief = "flat"
                        btn_bd = 0

                    btn = tk.Button(
                        grid,
                        text=str(d.day),
                        command=lambda target=d: _choose(target),
                        font=btn_font,
                        bg=btn_bg,
                        fg=btn_fg,
                        activebackground=btn_ab,
                        activeforeground=btn_fg,
                        relief=btn_relief,
                        bd=btn_bd,
                        padx=2,
                        pady=2,
                        cursor="hand2",
                    )
                    btn.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")

                    # Hover effect for unselected buttons
                    if not is_sel:
                        def _on_enter(e, b=btn, h_bg=cfg.C("border") if is_cur_month else cfg.C("card2")):
                            b.configure(bg=h_bg)
                        def _on_leave(e, b=btn, orig_bg=btn_bg):
                            b.configure(bg=orig_bg)
                        btn.bind("<Enter>", _on_enter)
                        btn.bind("<Leave>", _on_leave)

        _render()

        # Keyboard and MouseWheel navigation
        def _move_focus(delta_days: int):
            new_date = focused_date["date"] + timedelta(days=delta_days)
            focused_date["date"] = new_date
            month_state["year"] = new_date.year
            month_state["month"] = new_date.month
            _render()

        def _on_key(event):
            if event.keysym == "Escape":
                _close()
            elif event.keysym in ("Return", "KP_Enter", "space"):
                _choose(focused_date["date"])
            elif event.keysym == "Left":
                _move_focus(-1)
            elif event.keysym == "Right":
                _move_focus(1)
            elif event.keysym == "Up":
                _move_focus(-7)
            elif event.keysym == "Down":
                _move_focus(7)
            elif event.keysym in ("Prior", "Page_Up"):
                _shift_month(-1)
            elif event.keysym in ("Next", "Page_Down"):
                _shift_month(1)
            elif event.keysym == "Home":
                _select_today()

        def _on_mousewheel(event):
            if event.delta > 0:
                _shift_month(-1)
            elif event.delta < 0:
                _shift_month(1)

        picker.bind("<Key>", _on_key)
        picker.bind("<MouseWheel>", _on_mousewheel)
        picker.protocol("WM_DELETE_WINDOW", _close)
        picker.grab_set()
        picker.focus_force()

    calendar_btn = make_button(row, "📅", command=_open_calendar, variant="secondary")
    calendar_btn.configure(width=3)
    calendar_btn.pack(side="left")
    return entry


def _labeled_time_entry(parent, label_text: str, textvariable: tk.StringVar) -> tk.Entry:
    """Pack a time entry with a clock button for choosing hours and minutes."""
    row = tk.Frame(parent, bg=cfg.C("card"))
    row.pack(fill="x", pady=(0, 10))
    tk.Label(
        row, text=label_text, font=cfg.FONT["xs_b"], bg=cfg.C("card"),
        fg=cfg.C("text2"), width=13, anchor="w",
    ).pack(side="left")
    entry = make_entry(row, textvariable=textvariable, width=24)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def _open_clock():
        try:
            time_text = format_time_12h(textvariable.get())
            hour_text, rest = time_text.split(":", 1)
            minute_text, period = rest.split()
            hour, minute = int(hour_text), int(minute_text)
            if not (1 <= hour <= 12 and 0 <= minute <= 59 and period in ("AM", "PM")):
                raise ValueError
        except (ValueError, TypeError):
            hour, minute, period = 9, 0, "AM"

        picker = tk.Toplevel(parent.winfo_toplevel())
        picker.title("Select time")
        picker.configure(bg=cfg.C("card"))
        picker.resizable(False, False)
        picker.transient(parent.winfo_toplevel())
        picker_w, picker_h = 290, 160
        screen_w = picker.winfo_screenwidth()
        screen_h = picker.winfo_screenheight()
        bx = clock_btn.winfo_rootx()
        by = clock_btn.winfo_rooty()
        bh = clock_btn.winfo_height()

        pos_x = bx
        if pos_x + picker_w > screen_w - 16:
            pos_x = screen_w - picker_w - 16
        if pos_x < 10:
            pos_x = 10

        pos_y = by + bh + 4
        if pos_y + picker_h > screen_h - 50:
            above_y = by - picker_h - 4
            if above_y >= 10:
                pos_y = above_y
            else:
                pos_y = max(10, screen_h - picker_h - 50)

        picker.geometry(f"{picker_w}x{picker_h}+{pos_x}+{pos_y}")
        apply_window_theme(picker, dark=(cfg.current_theme_name() == "dark"))

        def _close():
            if picker.winfo_exists():
                picker.destroy()
            try:
                parent.winfo_toplevel().grab_set()
            except tk.TclError:
                pass

        controls = tk.Frame(picker, bg=cfg.C("card"))
        controls.pack(expand=True, pady=(18, 8))
        hour_var = tk.StringVar(value=str(hour))
        minute_var = tk.StringVar(value=f"{minute:02d}")
        period_var = tk.StringVar(value=period)
        _styled_combobox(controls, hour_var, [str(h) for h in range(1, 13)]).pack(side="left")
        tk.Label(controls, text=":", font=cfg.FONT["lg_b"], bg=cfg.C("card"), fg=cfg.C("text")).pack(side="left", padx=4)
        minute_picker = tk.Spinbox(
            controls, from_=0, to=59, wrap=True, width=3, format="%02.0f",
            textvariable=minute_var, font=cfg.FONT["sm_b"], justify="center",
            bg=cfg.C("card2"), fg=cfg.C("text"), buttonbackground=cfg.C("card2"),
            relief="flat", highlightthickness=1, highlightbackground=cfg.C("border"),
        )
        minute_picker.pack(side="left")
        _styled_combobox(controls, period_var, ["AM", "PM"]).pack(side="left", padx=(6, 0))

        def _set_time():
            try:
                chosen_hour = int(hour_var.get())
                chosen_minute = int(minute_var.get())
                if not (1 <= chosen_hour <= 12 and 0 <= chosen_minute <= 59):
                    raise ValueError
            except ValueError:
                chosen_hour, chosen_minute = hour, minute
                hour_var.set(str(hour))
                minute_var.set(f"{minute:02d}")
            textvariable.set(f"{chosen_hour:02d}:{chosen_minute:02d} {period_var.get()}")
            _close()

        make_button(picker, "Set time", command=_set_time, variant="primary").pack(pady=(0, 12))
        picker.protocol("WM_DELETE_WINDOW", _close)
        picker.bind("<Escape>", lambda _event: _close())
        picker.grab_set()
        picker.focus_force()

    clock_btn = make_button(row, "🕒", command=_open_clock, variant="secondary")
    clock_btn.configure(width=3)
    clock_btn.pack(side="left")
    return entry


def _styled_combobox(parent, variable, choices):
    """OptionMenu styled to match the dark/light palette with custom dropdown menu."""
    om = tk.OptionMenu(parent, variable, *choices)
    om.configure(
        bg=cfg.C("card2"),
        fg=cfg.C("text"),
        activebackground=cfg.C("accent"),
        activeforeground="#ffffff",
        highlightthickness=1,
        highlightbackground=cfg.C("border"),
        relief="flat",
        bd=0,
        font=cfg.FONT["sm_b"],
        padx=10,
        pady=4,
        cursor="hand2",
    )
    menu = om["menu"]
    menu.configure(
        bg=cfg.C("card2"),
        fg=cfg.C("text"),
        activebackground=cfg.C("accent"),
        activeforeground="#ffffff",
        font=cfg.FONT["sm"],
        bd=1,
        relief="flat",
    )
    return om


# ── Note Dialog ──────────────────────────────────────────────────────────────

class NoteDialog:
    COLORS = ["violet", "cyan", "green", "amber", "rose"]

    def __init__(self, parent, on_save, note=None):
        self._parent   = parent
        self._on_save  = on_save
        self._editing  = note

        self._title_var    = tk.StringVar(value=note.get("title", "")    if note else "")
        self._category_var = tk.StringVar(value=note.get("category", "") if note else "")
        self._tags_var     = tk.StringVar(value=", ".join(note.get("tags", [])) if note else "")
        self._color_var    = tk.StringVar(value=note.get("color", "violet") if note else "violet")

        self._win = _modal_window(parent, "Edit Note" if note else "New Note", width=520, height=580)
        self._build()

    def _build(self):
        win = self._win

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Label(
            win,
            text="✏ Edit Note" if self._editing else "✨ New Note",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        )
        header.pack(side="top", padx=24, pady=(20, 12), anchor="w")

        # ── Fixed bottom action buttons (always visible) ──────────────────
        btn_row = tk.Frame(win, bg=cfg.C("card"))
        btn_row.pack(side="bottom", fill="x", padx=24, pady=16)

        make_button(btn_row, "Cancel", command=self._win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
        make_button(btn_row, "Save Note", command=self._save, variant="primary").pack(side="right")

        # ── Scrollable or flexible body ───────────────────────────────────
        body = tk.Frame(win, bg=cfg.C("card"))
        body.pack(side="top", fill="both", expand=True, padx=24)

        # Fields
        _labeled_entry(body, "Title", self._title_var)
        _labeled_entry(body, "Category", self._category_var)
        _labeled_entry(body, "Tags (csv)", self._tags_var)

        # Color picker pills
        color_row = tk.Frame(body, bg=cfg.C("card"))
        color_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            color_row, text="Color", font=cfg.FONT["xs_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"), width=13, anchor="w",
        ).pack(side="left")

        for c in self.COLORS:
            fg, bg = cfg.color_pair(c)
            rb = tk.Radiobutton(
                color_row,
                text=f"● {c.capitalize()}",
                variable=self._color_var,
                value=c,
                indicatoron=False,
                bg=cfg.C("card2"),
                fg=fg,
                selectcolor=bg,
                activebackground=cfg.C("border"),
                activeforeground=fg,
                font=cfg.FONT["xs_b"],
                relief="flat",
                bd=0,
                padx=8,
                pady=4,
                cursor="hand2",
            )
            rb.pack(side="left", padx=2)

        # Description / body text
        tk.Label(
            body, text="Description", font=cfg.FONT["xs_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"), anchor="w",
        ).pack(anchor="w", pady=(4, 2))

        self._desc_text = make_text(body, height=7, width=36)
        self._desc_text.pack(fill="both", expand=True)
        if self._editing:
            self._desc_text.insert("1.0", self._editing.get("description", ""))

    def _save(self):
        payload = {
            "title":       self._title_var.get().strip() or "Untitled",
            "description": self._desc_text.get("1.0", "end-1c"),
            "category":    self._category_var.get().strip() or "General",
            "tags":        [t.strip() for t in self._tags_var.get().split(",") if t.strip()],
            "color":       self._color_var.get(),
        }
        self._on_save(payload)
        self._win.destroy()


# ── Task Dialog ──────────────────────────────────────────────────────────────

class TaskDialog:
    PRIORITIES = ["High", "Medium", "Low"]
    STATUSES   = ["Todo", "In Progress", "Completed"]

    def __init__(self, parent, on_save, task=None):
        self._parent   = parent
        self._on_save  = on_save
        self._editing  = task

        self._title_var    = tk.StringVar(value=task.get("title", "")    if task else "")
        self._category_var = tk.StringVar(value=task.get("category", "") if task else "")
        self._due_var      = tk.StringVar(value=task.get("dueDate", date.today().isoformat()) if task else date.today().isoformat())
        self._priority_var = tk.StringVar(value=task.get("priority", "Medium") if task else "Medium")
        self._status_var   = tk.StringVar(value=task.get("status",   "Todo")   if task else "Todo")

        self._win = _modal_window(parent, "Edit Task" if task else "New Task", width=520, height=540)
        self._build()

    def _build(self):
        win = self._win

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Label(
            win,
            text="✏ Edit Task" if self._editing else "✅ New Task",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        )
        header.pack(side="top", padx=24, pady=(20, 12), anchor="w")

        # ── Fixed bottom action buttons (always visible) ──────────────────
        btn_row = tk.Frame(win, bg=cfg.C("card"))
        btn_row.pack(side="bottom", fill="x", padx=24, pady=16)

        make_button(btn_row, "Cancel", command=self._win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
        make_button(btn_row, "Save Task", command=self._save, variant="primary").pack(side="right")

        # ── Body ──────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=cfg.C("card"))
        body.pack(side="top", fill="both", expand=True, padx=24)

        _labeled_entry(body, "Title", self._title_var)
        _labeled_entry(body, "Category", self._category_var)
        _labeled_date_entry(body, "Due Date", self._due_var)

        # Priority row
        prow = tk.Frame(body, bg=cfg.C("card"))
        prow.pack(fill="x", pady=(0, 10))
        tk.Label(
            prow, text="Priority", font=cfg.FONT["xs_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"), width=13, anchor="w",
        ).pack(side="left")
        _styled_combobox(prow, self._priority_var, self.PRIORITIES).pack(side="left", fill="x", expand=True)

        # Status row
        srow = tk.Frame(body, bg=cfg.C("card"))
        srow.pack(fill="x", pady=(0, 10))
        tk.Label(
            srow, text="Status", font=cfg.FONT["xs_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"), width=13, anchor="w",
        ).pack(side="left")
        _styled_combobox(srow, self._status_var, self.STATUSES).pack(side="left", fill="x", expand=True)

        # Description
        tk.Label(
            body, text="Description", font=cfg.FONT["xs_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"), anchor="w",
        ).pack(anchor="w", pady=(4, 2))

        self._desc_text = make_text(body, height=4, width=36)
        self._desc_text.pack(fill="both", expand=True)
        if self._editing:
            self._desc_text.insert("1.0", self._editing.get("description", ""))

    def _save(self):
        payload = {
            "title":       self._title_var.get().strip() or "Untitled",
            "description": self._desc_text.get("1.0", "end-1c"),
            "category":    self._category_var.get().strip() or "General",
            "dueDate":     self._due_var.get().strip(),
            "priority":    self._priority_var.get(),
            "status":      self._status_var.get(),
        }
        self._on_save(payload)
        self._win.destroy()


# ── Event Dialog ─────────────────────────────────────────────────────────────

class EventDialog:
    def __init__(self, parent, on_save, event=None, default_date=""):
        self._parent   = parent
        self._on_save  = on_save
        self._editing  = event

        def_d = default_date or date.today().isoformat()
        self._title_var    = tk.StringVar(value=event.get("title", "") if event else "")
        self._date_var     = tk.StringVar(value=event.get("date", def_d) if event else def_d)
        self._time_var     = tk.StringVar(value=format_time_12h(event.get("time", "09:00 AM")) if event else "09:00 AM")
        self._reminder_var = tk.BooleanVar(value=event.get("reminder", False) if event else False)

        self._win = _modal_window(parent, "Edit Event" if event else "New Event", width=480, height=480)
        self._build()

    def _build(self):
        win = self._win

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Label(
            win,
            text="✏ Edit Event" if self._editing else "📅 New Event",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        )
        header.pack(side="top", padx=24, pady=(20, 12), anchor="w")

        # ── Fixed bottom action buttons (always visible) ──────────────────
        btn_row = tk.Frame(win, bg=cfg.C("card"))
        btn_row.pack(side="bottom", fill="x", padx=24, pady=16)

        make_button(btn_row, "Cancel", command=self._win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
        make_button(btn_row, "Save Event", command=self._save, variant="primary").pack(side="right")

        # ── Body ──────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=cfg.C("card"))
        body.pack(side="top", fill="both", expand=True, padx=24)

        _labeled_entry(body, "Title", self._title_var)
        _labeled_date_entry(body, "Date", self._date_var)
        _labeled_time_entry(body, "Time", self._time_var)

        # Description
        tk.Label(
            body, text="Description", font=cfg.FONT["xs_b"],
            bg=cfg.C("card"), fg=cfg.C("text2"), anchor="w",
        ).pack(anchor="w", pady=(4, 2))

        self._desc_text = make_text(body, height=4, width=36)
        self._desc_text.pack(fill="both", expand=True)
        if self._editing:
            self._desc_text.insert("1.0", self._editing.get("description", ""))

        # Reminder checkbox
        tk.Checkbutton(
            body,
            text="Set reminder alert",
            variable=self._reminder_var,
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            selectcolor=cfg.C("card2"),
            activebackground=cfg.C("card"),
            activeforeground=cfg.C("text"),
            font=cfg.FONT["sm"],
            relief="flat",
            bd=0,
        ).pack(anchor="w", pady=(8, 0))

    def _save(self):
        payload = {
            "title":       self._title_var.get().strip() or "Untitled",
            "date":        self._date_var.get().strip(),
            "time":        format_time_12h(self._time_var.get().strip()),
            "description": self._desc_text.get("1.0", "end-1c"),
            "reminder":    self._reminder_var.get(),
        }
        self._on_save(payload)
        self._win.destroy()


# ── Confirm Dialog ───────────────────────────────────────────────────────────

def confirm(parent, message: str, on_confirm):
    """Modern modal confirmation dialog with dark/light styling."""
    win = _modal_window(parent, "Confirm Action", width=420, height=180)

    btn_row = tk.Frame(win, bg=cfg.C("card"))
    btn_row.pack(side="bottom", fill="x", padx=24, pady=16)

    make_button(btn_row, "Cancel", command=win.destroy, variant="ghost").pack(side="right", padx=(8, 0))

    def _yes():
        win.destroy()
        on_confirm()

    make_button(btn_row, "Confirm", command=_yes, variant="danger").pack(side="right")

    msg_lbl = tk.Label(
        win,
        text=message,
        font=cfg.FONT["base"],
        bg=cfg.C("card"),
        fg=cfg.C("text"),
        wraplength=370,
        justify="left",
    )
    msg_lbl.pack(side="top", fill="both", expand=True, padx=24, pady=(24, 0), anchor="w")
