"""
OneDesk Tasks View — tasks_view.py
List view with filter pills + inline add, and Kanban board view.
"""

import tkinter as tk
from datetime import date
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_separator, ScrollableFrame,
)
from ..components.modals import TaskDialog, confirm


COLUMNS = ["Todo", "In Progress", "Completed"]


class TasksView(tk.Frame):
    def __init__(self, parent, store, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store        = store
        self._filter       = "All"
        self._view         = "list"   # "list" | "kanban"
        self._search_query = ""

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
        pct       = self._store.completion_pct
        tk.Label(trow, text=f"  {completed}/{total} done ({pct}%)",
                 font=cfg.FONT["sm"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(side="left", pady=(6, 0))
        make_button(trow, text="+ New Task", command=self._open_new, variant="primary").pack(side="right")

        # Filter pills + search box + view toggle
        controls = tk.Frame(self._header, bg=cfg.C("bg"))
        controls.pack(fill="x", pady=(10, 0))

        for f in ["All"] + COLUMNS:
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
            tk.Label(row, text=f"📅 {task['dueDate']}", font=cfg.FONT["xs"],
                     bg=cfg.C("card"), fg=cfg.C("text3")).pack(side="left", padx=4)
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
                self._make_kanban_card(inner, task)

    def _make_kanban_card(self, parent, task: dict):
        card = tk.Frame(parent, bg=cfg.C("bg"),
                         highlightthickness=1, highlightbackground=cfg.C("border"))
        card.pack(fill="x", pady=4)
        inner = tk.Frame(card, bg=cfg.C("bg"), padx=12, pady=10)
        inner.pack(fill="x")

        tk.Label(inner, text=task.get("title", ""), font=cfg.FONT["sm_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text"), anchor="w",
                 wraplength=220).pack(anchor="w")

        meta = tk.Frame(inner, bg=cfg.C("bg"))
        meta.pack(anchor="w", pady=(4, 0))
        if task.get("dueDate"):
            tk.Label(meta, text=f"📅 {task['dueDate']}", font=cfg.FONT["xs"],
                     bg=cfg.C("bg"), fg=cfg.C("text3")).pack(side="left")

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

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _filtered_tasks(self):
        tasks = self._store.tasks
        if self._filter != "All":
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
