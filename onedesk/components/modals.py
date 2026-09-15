"""
OneDesk Modals — modals.py
Reusable Toplevel dialogs for Notes, Tasks, and Events.
"""

import tkinter as tk
from .. import config as cfg
from .ui_helpers import make_button, make_entry, make_text, make_label


def _labeled_row(parent, label_text, widget):
    """Pack a (Label, widget) pair as a horizontal row."""
    row = tk.Frame(parent, bg=cfg.C("card"))
    row.pack(fill="x", pady=(0, 8))
    tk.Label(
        row,
        text=label_text,
        font=cfg.FONT["xs_b"],
        bg=cfg.C("card"),
        fg=cfg.C("text2"),
        width=12,
        anchor="w",
    ).pack(side="left")
    widget.configure(bg=cfg.C("card2")) if hasattr(widget, "configure") else None
    widget.pack(side="left", fill="x", expand=True)
    return row


def _styled_combobox(parent, variable, choices):
    """Simple OptionMenu styled to match the dark palette."""
    om = tk.OptionMenu(parent, variable, *choices)
    om.configure(
        bg=cfg.C("card2"),
        fg=cfg.C("text"),
        activebackground=cfg.C("card2"),
        activeforeground=cfg.C("text"),
        highlightthickness=0,
        relief="flat",
        font=cfg.FONT["sm"],
        padx=6, pady=3,
    )
    om["menu"].configure(
        bg=cfg.C("card2"),
        fg=cfg.C("text"),
        activebackground=cfg.C("accent"),
        activeforeground="#fff",
        font=cfg.FONT["sm"],
    )
    return om


def _modal_window(parent, title, width=480, height=520):
    """Create and centre a modal Toplevel."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=cfg.C("card"))
    win.resizable(False, False)
    win.grab_set()

    px = parent.winfo_rootx() + (parent.winfo_width()  - width)  // 2
    py = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    win.geometry(f"{width}x{height}+{max(0, px)}+{max(0, py)}")
    return win


# ── Note Dialog ──────────────────────────────────────────────────────────────

class NoteDialog:
    COLORS = ["violet", "cyan", "green", "amber", "rose"]

    def __init__(self, parent, on_save, note=None):
        """
        on_save(fields: dict) — called with the note payload.
        note — existing note dict for editing, None for new.
        """
        self._parent   = parent
        self._on_save  = on_save
        self._editing  = note

        self._title_var    = tk.StringVar(value=note.get("title", "")    if note else "")
        self._category_var = tk.StringVar(value=note.get("category", "") if note else "")
        self._tags_var     = tk.StringVar(value=", ".join(note.get("tags", [])) if note else "")
        self._color_var    = tk.StringVar(value=note.get("color", "violet") if note else "violet")

        self._win = _modal_window(parent, "Edit Note" if note else "New Note", 480, 540)
        self._build()

    def _build(self):
        win = self._win
        header = tk.Label(
            win,
            text="✏ Edit Note" if self._editing else "✨ New Note",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        )
        header.pack(padx=24, pady=(20, 14), anchor="w")

        body = tk.Frame(win, bg=cfg.C("card"))
        body.pack(fill="both", expand=True, padx=24)

        # Title
        _labeled_row(body, "Title", make_entry(body, self._title_var))

        # Category
        _labeled_row(body, "Category", make_entry(body, self._category_var))

        # Tags
        _labeled_row(body, "Tags (csv)", make_entry(body, self._tags_var))

        # Color picker
        color_row = tk.Frame(body, bg=cfg.C("card"))
        color_row.pack(fill="x", pady=(0, 8))
        tk.Label(color_row, text="Color", font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text2"), width=12, anchor="w").pack(side="left")
        for c in self.COLORS:
            fg, bg = cfg.color_pair(c)
            rb = tk.Radiobutton(
                color_row, text=c.capitalize(),
                variable=self._color_var, value=c,
                bg=cfg.C("card"), fg=fg, selectcolor=bg,
                activebackground=cfg.C("card"),
                font=cfg.FONT["xs_b"], relief="flat",
            )
            rb.pack(side="left", padx=2)

        # Description / body text
        tk.Label(body, text="Description", font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text2"), anchor="w").pack(anchor="w", pady=(4, 2))
        self._desc_text = make_text(body, height=8)
        self._desc_text.pack(fill="both", expand=True)
        if self._editing:
            self._desc_text.insert("1.0", self._editing.get("description", ""))

        # Buttons
        btn_row = tk.Frame(win, bg=cfg.C("card"))
        btn_row.pack(fill="x", padx=24, pady=16)
        make_button(btn_row, "Cancel", command=self._win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
        make_button(btn_row, "Save Note", command=self._save, variant="primary").pack(side="right")

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
        self._due_var      = tk.StringVar(value=task.get("dueDate", "")  if task else "")
        self._priority_var = tk.StringVar(value=task.get("priority", "Medium") if task else "Medium")
        self._status_var   = tk.StringVar(value=task.get("status",   "Todo")   if task else "Todo")

        self._win = _modal_window(parent, "Edit Task" if task else "New Task", 480, 460)
        self._build()

    def _build(self):
        win = self._win
        tk.Label(
            win,
            text="✏ Edit Task" if self._editing else "✅ New Task",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(padx=24, pady=(20, 14), anchor="w")

        body = tk.Frame(win, bg=cfg.C("card"))
        body.pack(fill="both", expand=True, padx=24)

        _labeled_row(body, "Title", make_entry(body, self._title_var))
        _labeled_row(body, "Category", make_entry(body, self._category_var))
        _labeled_row(body, "Due Date", make_entry(body, self._due_var))

        # Priority
        prow = tk.Frame(body, bg=cfg.C("card"))
        prow.pack(fill="x", pady=(0, 8))
        tk.Label(prow, text="Priority", font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text2"), width=12, anchor="w").pack(side="left")
        _styled_combobox(prow, self._priority_var, self.PRIORITIES).pack(side="left", fill="x", expand=True)

        # Status
        srow = tk.Frame(body, bg=cfg.C("card"))
        srow.pack(fill="x", pady=(0, 8))
        tk.Label(srow, text="Status", font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text2"), width=12, anchor="w").pack(side="left")
        _styled_combobox(srow, self._status_var, self.STATUSES).pack(side="left", fill="x", expand=True)

        # Description
        tk.Label(body, text="Description", font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text2"), anchor="w").pack(anchor="w", pady=(4, 2))
        self._desc_text = make_text(body, height=5)
        self._desc_text.pack(fill="both", expand=True)
        if self._editing:
            self._desc_text.insert("1.0", self._editing.get("description", ""))

        # Buttons
        btn_row = tk.Frame(win, bg=cfg.C("card"))
        btn_row.pack(fill="x", padx=24, pady=16)
        make_button(btn_row, "Cancel", command=self._win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
        make_button(btn_row, "Save Task", command=self._save, variant="primary").pack(side="right")

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

        self._title_var    = tk.StringVar(value=event.get("title", "")  if event else "")
        self._date_var     = tk.StringVar(value=event.get("date", default_date)  if event else default_date)
        self._time_var     = tk.StringVar(value=event.get("time", "09:00") if event else "09:00")
        self._reminder_var = tk.BooleanVar(value=event.get("reminder", False) if event else False)

        self._win = _modal_window(parent, "Edit Event" if event else "New Event", 460, 380)
        self._build()

    def _build(self):
        win = self._win
        tk.Label(
            win,
            text="✏ Edit Event" if self._editing else "📅 New Event",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(padx=24, pady=(20, 14), anchor="w")

        body = tk.Frame(win, bg=cfg.C("card"))
        body.pack(fill="both", expand=True, padx=24)

        _labeled_row(body, "Title",      make_entry(body, self._title_var))
        _labeled_row(body, "Date",       make_entry(body, self._date_var))
        _labeled_row(body, "Time (HH:MM)", make_entry(body, self._time_var))

        # Description
        tk.Label(body, text="Description", font=cfg.FONT["xs_b"], bg=cfg.C("card"), fg=cfg.C("text2"), anchor="w").pack(anchor="w", pady=(4, 2))
        self._desc_text = make_text(body, height=4)
        self._desc_text.pack(fill="both", expand=True)
        if self._editing:
            self._desc_text.insert("1.0", self._editing.get("description", ""))

        # Reminder checkbox
        tk.Checkbutton(
            body,
            text="Set reminder",
            variable=self._reminder_var,
            bg=cfg.C("card"), fg=cfg.C("text"),
            selectcolor=cfg.C("card2"),
            activebackground=cfg.C("card"),
            font=cfg.FONT["sm"],
        ).pack(anchor="w", pady=(6, 0))

        # Buttons
        btn_row = tk.Frame(win, bg=cfg.C("card"))
        btn_row.pack(fill="x", padx=24, pady=16)
        make_button(btn_row, "Cancel", command=self._win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
        make_button(btn_row, "Save Event", command=self._save, variant="primary").pack(side="right")

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

def confirm(parent, message, on_confirm):
    win = _modal_window(parent, "Confirm", 380, 160)
    tk.Label(win, text=message, font=cfg.FONT["base"], bg=cfg.C("card"), fg=cfg.C("text"),
             wraplength=330, justify="left").pack(padx=24, pady=(24, 12), anchor="w")
    btn_row = tk.Frame(win, bg=cfg.C("card"))
    btn_row.pack(fill="x", padx=24)
    make_button(btn_row, "Cancel", command=win.destroy, variant="ghost").pack(side="right", padx=(8, 0))
    def _yes():
        on_confirm()
        win.destroy()
    make_button(btn_row, "Confirm", command=_yes, variant="danger").pack(side="right")
