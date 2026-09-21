"""
OneDesk Modals — modals.py
Reusable Toplevel dialogs for Notes, Tasks, Events, and Confirmations.
Styled for Windows native dark/light modes with pinned action bars and responsive layouts.
"""

from datetime import date
import tkinter as tk
from .. import config as cfg
from ..platform_helpers import apply_window_theme, center_window
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
    """Pack a (Label, Date Entry, 'Today' button) row."""
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
    entry = make_entry(row, textvariable=textvariable, width=20)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def _set_today():
        textvariable.set(date.today().isoformat())

    make_button(row, "Today", command=_set_today, variant="secondary").pack(side="left")
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
        self._time_var     = tk.StringVar(value=event.get("time", "09:00") if event else "09:00")
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
        _labeled_entry(body, "Time (HH:MM)", self._time_var)

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
            "time":        self._time_var.get().strip(),
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
