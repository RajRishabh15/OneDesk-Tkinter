"""
OneDesk Tasks View — tasks_view.py
List view with filter pills + inline add, and Kanban board view.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import date
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_separator, ScrollableFrame,
)
from ..components.modals import TaskDialog, confirm
from ..importers import parse_tasks_file


COLUMNS = ["Todo", "In Progress", "Completed"]


class TasksView(tk.Frame):
    def __init__(self, parent, store, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store        = store
        self._filter       = "All"
        self._view         = "list"   # "list" | "kanban"
        self._search_query = ""
        self._drag = None
        self._kanban_columns = {}
        self._drag_preview = None

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
        self._body.pack(fill="both", expand=True)
        self._render_body()

    def _render_header(self):
        for w in self._header.winfo_children():
            w.destroy()

        # Title row
        trow = tk.Frame(self._header, bg=cfg.C("bg"))
        trow.pack(fill="x")
        tk.Label(trow, text="Tasks", font=cfg.FONT["2xl_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text")).pack(side="left")
        completed = len(self._store.completed_tasks)
        total     = len(self._store.tasks)
        overdue = len(self._store.overdue_tasks)
        pct       = self._store.completion_pct
        tk.Label(trow, text=f"  {completed}/{total} done ({pct}%) · {overdue} overdue",
                 font=cfg.FONT["sm"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(side="left", pady=(6, 0))
        t_btns = tk.Frame(trow, bg=cfg.C("bg"))
        t_btns.pack(side="right")

        make_button(
            t_btns, text="📥 Import Tasks",
            command=self._import_tasks,
            variant="secondary",
        ).pack(side="left", padx=(0, 8))

        make_button(
            t_btns, text="+ New Task",
            command=self._open_new,
            variant="primary",
        ).pack(side="left")

        # Filter pills + search box + view toggle
        controls = tk.Frame(self._header, bg=cfg.C("bg"))
        controls.pack(fill="x", pady=(10, 0))

        for f in ["All" , "Overdue"] + COLUMNS:
            active = (f == self._filter)
            tk.Button(
                controls, text=f, font=cfg.FONT["xs_b"],
                fg=cfg.C("text") if active else cfg.C("text2"),
                bg=cfg.C("accent") if active else cfg.C("card2"),
                activeforeground=cfg.C("text"), activebackground=cfg.C("accent"),
                relief="flat", bd=0, padx=12, pady=4, cursor="hand2",
                command=lambda fi=f: self._set_filter(fi),
            ).pack(side="left", padx=2)

        # Inline search input for tasks
        search_box = tk.Frame(
            controls,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )
        search_box.pack(side="left", padx=(16, 0))
        tk.Label(
            search_box, text="🔍", font=cfg.FONT["xs"],
            bg=cfg.C("card2"), fg=cfg.C("text3"),
        ).pack(side="left", padx=(6, 2))

        self._search_entry = tk.Entry(
            search_box,
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            width=20,
        )
        self._search_entry.pack(side="left", padx=(0, 6), ipady=3)
        if self._search_query:
            self._search_entry.insert(0, self._search_query)
        self._search_entry.bind("<KeyRelease>", self._on_search_input)

        # View toggle
        for label, mode in [("≡ List", "list"), ("⊞ Kanban", "kanban")]:
            active = (mode == self._view)
            tk.Button(
                controls, text=label, font=cfg.FONT["xs_b"],
                fg=cfg.C("text") if active else cfg.C("text2"),
                bg=cfg.C("card2") if not active else cfg.C("card"),
                activeforeground=cfg.C("text"), activebackground=cfg.C("card2"),
                relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                command=lambda m=mode: self._set_view(m),
            ).pack(side="right", padx=2)

    def _render_body(self):
        for w in self._body.winfo_children():
            w.destroy()
        if self._view == "list":
            self._render_list()
        else:
            self._render_kanban()

    def _refresh(self):
        self._render_header()
        self._render_body()

    # ── List View ────────────────────────────────────────────────────────────
    def _render_list(self):
        scroll = ScrollableFrame(self._body, bg=cfg.C("bg"))
        scroll.pack(fill="both", expand=True, padx=cfg.PAD, pady=cfg.PAD)
        inner = scroll.inner

        tasks = self._filtered_tasks()

        # Inline quick-add
        inline = tk.Frame(inner, bg=cfg.C("card"),
                           highlightthickness=1, highlightbackground=cfg.C("border"))
        inline.pack(fill="x", pady=(0, 8))
        irow = tk.Frame(inline, bg=cfg.C("card"), padx=12, pady=8)
        irow.pack(fill="x")
        self._inline_var = tk.StringVar()
        e = tk.Entry(irow, textvariable=self._inline_var, font=cfg.FONT["sm"],
                     bg=cfg.C("card2"), fg=cfg.C("text"), insertbackground=cfg.C("text"),
                     relief="flat", bd=0, highlightthickness=1, highlightbackground=cfg.C("border"))
        e.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))
        e.bind("<Return>", self._quick_add)
        _placeholder(e, "Quick-add a task and press Enter…", cfg.C("text3"))
        make_button(irow, "Add", command=self._quick_add, variant="secondary").pack(side="left")
        make_button(irow, "+ Detailed", command=self._open_new, variant="ghost").pack(side="left", padx=(6, 0))

        if not tasks:
            tk.Label(inner, text="✅  No tasks here. You're all caught up!",
                     font=cfg.FONT["lg"], bg=cfg.C("bg"), fg=cfg.C("text2"), pady=40).pack()
            return

        for task in tasks:
            self._make_task_row(inner, task)

    def _make_task_row(self, parent, task: dict):
        card = tk.Frame(parent, bg=cfg.C("card"),
                         highlightthickness=1, highlightbackground=cfg.C("border"))
        card.pack(fill="x", pady=3)

        row = tk.Frame(card, bg=cfg.C("card"), padx=14, pady=10)
        row.pack(fill="x")

        # Priority accent bar
        pcolor = cfg.PRIORITY_FG.get(task.get("priority", ""), cfg.C("border"))
        tk.Frame(card, bg=pcolor, width=3).place(relx=0, rely=0, relheight=1)

        # Complete toggle checkbox
        done = task.get("status") == "Completed"
        done_var = tk.BooleanVar(value=done)
        chk = tk.Checkbutton(
            row, variable=done_var, bg=cfg.C("card"),
            activebackground=cfg.C("card"), selectcolor=cfg.C("card2"),
            relief="flat", bd=0, highlightthickness=0, cursor="hand2",
            command=lambda tid=task["id"]: self._store.toggle_complete(tid),
        )
        chk.pack(side="left", padx=(0, 4))

        # Title
        title_fg = cfg.C("text2") if done else cfg.C("text")
        tk.Label(row, text=task.get("title", ""), font=cfg.FONT["sm_b"],
                 bg=cfg.C("card"), fg=title_fg).pack(side="left", padx=(4, 12))

        # Meta info
        if task.get("dueDate"):
            is_overdue = (
            task.get("status") != "Completed"
            and task["dueDate"] < date.today().isoformat()
            )
            due_fg = cfg.C("danger") if is_overdue else cfg.C("text3")
            due_text = "⚠ " if is_overdue else "📅 "
            tk.Label(
                row,
                text=f"{due_text}{task['dueDate']}",
                font=cfg.FONT["xs_b"] if is_overdue else cfg.FONT["xs"],
                bg=cfg.C("card"),
                fg=due_fg,
            ).pack(side="left", padx=4)
        if task.get("category"):
            tk.Label(row, text=task["category"], font=cfg.FONT["xs"],
                     bg=cfg.C("card2"), fg=cfg.C("text2"), padx=6, pady=1).pack(side="left", padx=4)

        # Priority badge
        pbg = cfg.PRIORITY_BG.get(task.get("priority", ""), cfg.C("card2"))
        pfg = cfg.PRIORITY_FG.get(task.get("priority", ""), cfg.C("text"))
        tk.Label(row, text=task.get("priority", ""), font=cfg.FONT["xs_b"],
                 bg=pbg, fg=pfg, padx=6, pady=1).pack(side="right", padx=4)

        # Edit / Delete
        tk.Button(row, text="✏", font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("text3"),
                  activebackground=cfg.C("card2"), relief="flat", cursor="hand2",
                  command=lambda t=task: self._open_edit(t)).pack(side="right")
        tk.Button(row, text="🗑", font=cfg.FONT["xs"], bg=cfg.C("card"), fg=cfg.C("danger"),
                  activebackground=cfg.C("card2"), relief="flat", cursor="hand2",
                  command=lambda t=task: confirm(
                      self, f"Delete '{t['title']}'?",
                      lambda tid=t["id"]: self._store.delete_task(tid)
                  )).pack(side="right")

    # ── Kanban View ───────────────────────────────────────────────────────────
    def _render_kanban(self):
        self._kanban_columns = {}
        col_frame = tk.Frame(self._body, bg=cfg.C("bg"))
        col_frame.pack(fill="both", expand=True, padx=cfg.PAD, pady=cfg.PAD)

        col_colors = {
            "Todo":        cfg.C("text3"),
            "In Progress": cfg.C("accent2"),
            "Completed":   cfg.C("success"),
        }

        for i, status in enumerate(COLUMNS):
            col = tk.Frame(col_frame, bg=cfg.C("card"),
                            highlightthickness=1, highlightbackground=cfg.C("border"))
            col.grid(row=0, column=i, padx=6, sticky="nsew")
            self._kanban_columns[status] = col
            col_frame.columnconfigure(i, weight=1)

            # Column header
            hdr = tk.Frame(col, bg=cfg.C("card2"), padx=14, pady=10)
            hdr.pack(fill="x")
            tasks_in_col = [t for t in self._filtered_tasks() if t.get("status") == status]
            tk.Label(hdr, text=f"{status}  {len(tasks_in_col)}",
                     font=cfg.FONT["sm_b"], bg=cfg.C("card2"),
                     fg=col_colors.get(status, cfg.C("text"))).pack(side="left")

            # Tasks in column
            scroll = ScrollableFrame(col, bg=cfg.C("card"))
            scroll.pack(fill="both", expand=True, padx=8, pady=8)
            inner = scroll.inner

            for task in tasks_in_col:
                self._make_kanban_card(inner, task, status)

    def _make_kanban_card(self, parent, task: dict, status: str):
        card = tk.Frame(parent, bg=cfg.C("bg"),
                         highlightthickness=1, highlightbackground=cfg.C("border"))
        card.pack(fill="x", pady=4)
        card.configure(cursor="fleur")
        inner = tk.Frame(card, bg=cfg.C("bg"), padx=12, pady=10)
        inner.pack(fill="x")

        tk.Label(inner, text=task.get("title", ""), font=cfg.FONT["sm_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text"), anchor="w",
                 wraplength=220).pack(anchor="w")

        meta = tk.Frame(inner, bg=cfg.C("bg"))
        meta.pack(anchor="w", pady=(4, 0))
        if task.get("dueDate"):
            is_overdue = (
                task.get("status") != "Completed"
                and task["dueDate"] < date.today().isoformat()
            )
            due_fg = cfg.C("danger") if is_overdue else cfg.C("text3")
            due_text = "⚠ " if is_overdue else "📅 "
            tk.Label(
                meta,
                text=f"{due_text}{task['dueDate']}",
                font=cfg.FONT["xs_b"] if is_overdue else cfg.FONT["xs"],
                bg=cfg.C("bg"),
                fg=due_fg,
            ).pack(side="left")

        pfg = cfg.PRIORITY_FG.get(task.get("priority", ""), cfg.C("text2"))
        pbg = cfg.PRIORITY_BG.get(task.get("priority", ""), cfg.C("card2"))
        tk.Label(meta, text=task.get("priority", ""), font=cfg.FONT["xs"],
                 bg=pbg, fg=pfg, padx=4).pack(side="right")

        btn_row = tk.Frame(inner, bg=cfg.C("bg"))
        btn_row.pack(anchor="w", pady=(4, 0))

        # Status cycle buttons
        for label, nstatus in [("→ Todo", "Todo"), ("→ In Prog", "In Progress"), ("→ Done", "Completed")]:
            if nstatus != task.get("status"):
                tk.Button(
                    btn_row, text=label, font=cfg.FONT["xs"],
                    bg=cfg.C("card"), fg=cfg.C("text2"),
                    activebackground=cfg.C("accent"), activeforeground="#fff",
                    relief="flat", bd=0, padx=4, pady=2, cursor="hand2",
                    command=lambda tid=task["id"], s=nstatus: self._store.set_task_status(tid, s),
                ).pack(side="left", padx=2)

        tk.Button(
            btn_row, text="✏", font=cfg.FONT["xs"], bg=cfg.C("bg"), fg=cfg.C("text3"),
            relief="flat", cursor="hand2",
            command=lambda t=task: self._open_edit(t),
        ).pack(side="right")

        # Bind the whole card so its labels and empty space can start a drag.
        self._bind_card_drag(card, task["id"], status)

    def _bind_card_drag(self, widget, task_id: str, source_status: str):
        widget.bind("<ButtonPress-1>",
                    lambda event, tid=task_id, src=source_status: self._drag_start(event, tid, src),
                    add="+")
        widget.bind("<B1-Motion>", self._drag_motion, add="+")
        widget.bind("<ButtonRelease-1>", self._drag_release, add="+")
        for child in widget.winfo_children():
            self._bind_card_drag(child, task_id, source_status)

    def _drag_start(self, event, task_id: str, source_status: str):
        self._drag = {
            "task_id": task_id,
            "source": source_status,
            "x": event.x_root,
            "y": event.y_root,
            "active": False,
            "target": None,
        }

    def _drag_motion(self, event):
        if not self._drag:
            return
        drag = self._drag
        if not drag["active"]:
            if abs(event.x_root - drag["x"]) + abs(event.y_root - drag["y"]) < 8:
                return
            drag["active"] = True
            self._show_drag_preview(drag["task_id"], event.x_root, event.y_root)
        elif self._drag_preview is not None:
            self._drag_preview.geometry(f"+{event.x_root + 14}+{event.y_root + 14}")
        target = None
        for status, column in self._kanban_columns.items():
            left, top = column.winfo_rootx(), column.winfo_rooty()
            if left <= event.x_root < left + column.winfo_width() and top <= event.y_root < top + column.winfo_height():
                target = status
                break
        drag["target"] = target
        for status, column in self._kanban_columns.items():
            column.configure(highlightbackground=(cfg.C("accent") if status == target else cfg.C("border")))

    def _drag_release(self, _event):
        drag, self._drag = self._drag, None
        if not drag:
            return
        self._hide_drag_preview()
        for column in self._kanban_columns.values():
            try:
                column.configure(highlightbackground=cfg.C("border"))
            except tk.TclError:
                pass
        if drag["active"]:
            target = drag["target"]
            if target and target != drag["source"]:
                self._store.set_task_status(drag["task_id"], target)
            return "break"

    def _show_drag_preview(self, task_id: str, x: int, y: int):
        task = next((item for item in self._store.tasks if item.get("id") == task_id), None)
        if not task:
            return
        preview = tk.Toplevel(self)
        preview.overrideredirect(True)
        preview.attributes("-topmost", True)
        preview.geometry(f"260x76+{x + 14}+{y + 14}")
        preview.configure(bg=cfg.C("bg"))
        preview.attributes("-alpha", 0.88)
        preview_frame = tk.Frame(
            preview, bg=cfg.C("bg"), padx=12, pady=10,
            highlightthickness=1, highlightbackground=cfg.C("accent"),
        )
        preview_frame.pack(fill="both", expand=True)
        tk.Label(
            preview_frame, text=task.get("title", ""), font=cfg.FONT["sm_b"],
            bg=cfg.C("bg"), fg=cfg.C("text"), anchor="w",
            wraplength=230,
        ).pack(anchor="w")
        tk.Label(
            preview_frame, text=f"{task.get('priority', '')}  ·  {task.get('status', '')}",
            font=cfg.FONT["xs"], bg=cfg.C("bg"), fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(4, 0))
        self._drag_preview = preview

    def _hide_drag_preview(self):
        if self._drag_preview is not None:
            try:
                self._drag_preview.destroy()
            except tk.TclError:
                pass
            self._drag_preview = None

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _filtered_tasks(self):
        tasks = self._store.tasks
        if self._filter == "Overdue":
            tasks = self._store.overdue_tasks
        elif self._filter != "All":
            tasks = [t for t in tasks if t.get("status") == self._filter]
        if self._search_query:
            q = self._search_query.lower()
            tasks = [
                t for t in tasks
                if q in t.get("title", "").lower()
                or q in t.get("description", "").lower()
                or q in t.get("category", "").lower()
            ]
        return tasks

    def _on_search_input(self, _event=None):
        self._search_query = self._search_entry.get().strip()
        self._render_body()

    def _set_filter(self, f: str):
        self._filter = f
        self._refresh()

    def _set_view(self, v: str):
        self._view = v
        self._refresh()

    def _open_new(self):
        TaskDialog(self, on_save=lambda f: self._store.add_task(**f))

    def _open_edit(self, task):
        def _save(fields, tid=task["id"]):
            self._store.update_task(tid, **fields)
        TaskDialog(self, on_save=_save, task=task)

    def _import_tasks(self):
        filetypes = [
            ("Supported Task Files", "*.json;*.csv;*.txt;*.md"),
            ("JSON files", "*.json"),
            ("CSV files", "*.csv"),
            ("Markdown & Text Checklists", "*.txt;*.md"),
            ("All files", "*.*"),
        ]
        paths = filedialog.askopenfilenames(
            title="Import Tasks",
            filetypes=filetypes,
        )
        if not paths:
            return

        total_imported = 0
        errors = []
        for path in paths:
            try:
                tasks = parse_tasks_file(path)
                count = self._store.import_tasks(tasks)
                total_imported += count
            except Exception as e:
                errors.append(f"{os.path.basename(path)}: {e}")

        if total_imported > 0:
            msg = f"Successfully imported {total_imported} task{'s' if total_imported != 1 else ''} into OneDesk!"
            if errors:
                msg += "\n\nWarnings/Errors:\n" + "\n".join(errors)
            messagebox.showinfo("Tasks Imported", msg)
        else:
            err_msg = "No valid tasks found to import."
            if errors:
                err_msg += "\n\nDetails:\n" + "\n".join(errors)
            messagebox.showwarning("Import Tasks", err_msg)

    def _quick_add(self, _event=None):
        text = self._inline_var.get().strip()
        if not text or text.startswith("Quick-add"):
            return
        self._store.add_task(
            title=text,
            priority="Medium",
            dueDate=date.today().isoformat(),
            status="Todo",
            category="General",
        )
        self._inline_var.set("")


def _placeholder(entry: tk.Entry, text: str, muted_fg: str):
    entry.insert(0, text)
    entry.configure(fg=muted_fg)

    def _in(e):
        if entry.get() == text:
            entry.delete(0, "end")
            entry.configure(fg=cfg.C("text"))

    def _out(e):
        if not entry.get():
            entry.insert(0, text)
            entry.configure(fg=muted_fg)

    entry.bind("<FocusIn>",  _in)
    entry.bind("<FocusOut>", _out)
