"""
OneDesk Search Popup — search_popup.py
Interactive live floating search dropdown overlay.
Displays categorized search results (Tasks, Notes, Events) directly beneath the search bar.
"""

import tkinter as tk
from .. import config as cfg
from ..components.modals import TaskDialog, NoteDialog, EventDialog


class SearchPopup:
    def __init__(self, anchor_widget, store, on_navigate=None):
        self._anchor = anchor_widget
        self._store = store
        self._on_navigate = on_navigate
        self._popup: tk.Toplevel | None = None
        self._visible = False

    def show(self, query: str):
        query = query.strip()
        if not query or query == "Search notes, tasks, events…":
            self.hide()
            return

        results = self._store.search(query)
        total = len(results["tasks"]) + len(results["notes"]) + len(results["events"])

        if self._popup is None or not self._popup.winfo_exists():
            self._create_popup()

        self._render_results(query, results, total)
        self._position()
        self._popup.deiconify()
        self._popup.lift()
        self._visible = True

    def hide(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.withdraw()
        self._visible = False

    def is_visible(self) -> bool:
        return self._visible and self._popup is not None and self._popup.winfo_exists()

    def destroy(self):
        if self._popup and self._popup.winfo_exists():
            try:
                self._popup.destroy()
            except Exception:
                pass
        self._popup = None
        self._visible = False

    def _create_popup(self):
        top = self._anchor.winfo_toplevel()
        self._popup = tk.Toplevel(top)
        self._popup.wm_overrideredirect(True)
        self._popup.configure(bg=cfg.C("border"))

        # Bind Esc to close
        self._popup.bind("<Escape>", lambda _: self.hide())
        top.bind("<Button-1>", self._check_click_outside, add="+")

    def _check_click_outside(self, event):
        if not self.is_visible():
            return
        try:
            px = self._popup.winfo_rootx()
            py = self._popup.winfo_rooty()
            pw = self._popup.winfo_width()
            ph = self._popup.winfo_height()
            x = event.x_root
            y = event.y_root
            if not (px <= x <= px + pw and py <= y <= py + ph):
                # Also don't hide if clicking inside search entry
                ax = self._anchor.winfo_rootx()
                ay = self._anchor.winfo_rooty()
                aw = self._anchor.winfo_width()
                ah = self._anchor.winfo_height()
                if not (ax <= x <= ax + aw and ay <= y <= ay + ah):
                    self.hide()
        except Exception:
            pass

    def _position(self):
        if not self._popup or not self._anchor.winfo_exists():
            return
        self._anchor.update_idletasks()
        ax = self._anchor.winfo_rootx()
        ay = self._anchor.winfo_rooty()
        aw = self._anchor.winfo_width()
        ah = self._anchor.winfo_height()

        width = max(aw + 120, 480)
        self._popup.update_idletasks()
        height = min(self._popup.winfo_reqheight(), 440)
        self._popup.geometry(f"{width}x{height}+{ax}+{ay + ah + 4}")

    def _render_results(self, query: str, results: dict, total: int):
        for w in self._popup.winfo_children():
            w.destroy()

        card = tk.Frame(
            self._popup,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("accent"),
        )
        card.pack(fill="both", expand=True)

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(card, bg=cfg.C("card"), padx=16, pady=10)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text=f"Search Results for \"{query}\"",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(side="left")
        tk.Label(
            hdr,
            text=f"{total} match{'es' if total != 1 else ''}",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=cfg.C("accent"),
            padx=8, pady=2,
        ).pack(side="right")

        tk.Frame(card, bg=cfg.C("border"), height=1).pack(fill="x")

        # Body container
        body = tk.Frame(card, bg=cfg.C("card"))
        body.pack(fill="both", expand=True, padx=8, pady=6)

        if total == 0:
            empty = tk.Frame(body, bg=cfg.C("card"), pady=24)
            empty.pack(fill="x")
            tk.Label(
                empty,
                text=f"🔍  No matching notes, tasks, or events found for \"{query}\"",
                font=cfg.FONT["sm"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
            ).pack()
        else:
            # ── Tasks Section ─────────────────────────────────────────────
            tasks = results["tasks"][:4]
            if tasks:
                self._section_label(body, "✓ TASKS", len(results["tasks"]))
                for task in tasks:
                    self._task_item(body, task)

            # ── Notes Section ─────────────────────────────────────────────
            notes = results["notes"][:4]
            if notes:
                self._section_label(body, "📝 NOTES", len(results["notes"]))
                for note in notes:
                    self._note_item(body, note)

            # ── Events Section ────────────────────────────────────────────
            events = results["events"][:3]
            if events:
                self._section_label(body, "📅 EVENTS", len(results["events"]))
                for event in events:
                    self._event_item(body, event)

        # ── Footer hint ───────────────────────────────────────────────────
        tk.Frame(card, bg=cfg.C("border"), height=1).pack(fill="x")
        footer = tk.Frame(card, bg=cfg.C("card2"), padx=14, pady=6)
        footer.pack(fill="x")
        tk.Label(
            footer,
            text="Press Enter to filter Notes view  •  Click item to view/edit  •  Esc to close",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
        ).pack(side="left")

    def _section_label(self, parent, text: str, count: int):
        row = tk.Frame(parent, bg=cfg.C("card"), pady=3)
        row.pack(fill="x", padx=4)
        tk.Label(
            row,
            text=f"{text} ({count})",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(anchor="w")

    def _task_item(self, parent, task: dict):
        item = tk.Frame(parent, bg=cfg.C("card2"), padx=10, pady=6, cursor="hand2")
        item.pack(fill="x", pady=2)

        # Checkbox / status
        done = task.get("status") == "Completed"
        status_color = cfg.STATUS_FG.get(task.get("status"), cfg.C("text2"))

        tk.Label(
            item,
            text="●",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=status_color,
        ).pack(side="left", padx=(0, 6))

        title_lbl = tk.Label(
            item,
            text=task.get("title", ""),
            font=cfg.FONT["sm_b" if not done else "sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text") if not done else cfg.C("text2"),
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        # Priority badge
        pfg = cfg.PRIORITY_FG.get(task.get("priority"), cfg.C("text2"))
        pbg = cfg.PRIORITY_BG.get(task.get("priority"), cfg.C("card"))
        tk.Label(
            item,
            text=task.get("priority", "Medium"),
            font=cfg.FONT["xs_b"],
            bg=pbg,
            fg=pfg,
            padx=6, pady=1,
        ).pack(side="right", padx=(4, 0))

        # Due date
        if task.get("dueDate"):
            tk.Label(
                item,
                text=task["dueDate"],
                font=cfg.FONT["xs"],
                bg=cfg.C("card2"),
                fg=cfg.C("text3"),
            ).pack(side="right", padx=(0, 6))

        # Hover & click
        def _click(e=None):
            self.hide()
            top = self._anchor.winfo_toplevel()
            TaskDialog(
                top,
                on_save=lambda f, tid=task["id"]: self._store.update_task(tid, **f),
                task=task,
            )

        item.bind("<Button-1>", _click)
        title_lbl.bind("<Button-1>", _click)
        item.bind("<Enter>", lambda _: item.configure(bg=cfg.C("border")))
        item.bind("<Leave>", lambda _: item.configure(bg=cfg.C("card2")))

    def _note_item(self, parent, note: dict):
        item = tk.Frame(parent, bg=cfg.C("card2"), padx=10, pady=6, cursor="hand2")
        item.pack(fill="x", pady=2)

        fg, bg = cfg.color_pair(note.get("color", "violet"))
        tk.Label(
            item,
            text="●",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=fg,
        ).pack(side="left", padx=(0, 6))

        title_lbl = tk.Label(
            item,
            text=note.get("title", "Untitled"),
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        if note.get("category"):
            tk.Label(
                item,
                text=note["category"],
                font=cfg.FONT["xs"],
                bg=cfg.C("card"),
                fg=cfg.C("text2"),
                padx=6, pady=1,
            ).pack(side="right", padx=(4, 0))

        def _click(e=None):
            self.hide()
            top = self._anchor.winfo_toplevel()
            NoteDialog(
                top,
                on_save=lambda f, nid=note["id"]: self._store.update_note(nid, **f),
                note=note,
            )

        item.bind("<Button-1>", _click)
        title_lbl.bind("<Button-1>", _click)
        item.bind("<Enter>", lambda _: item.configure(bg=cfg.C("border")))
        item.bind("<Leave>", lambda _: item.configure(bg=cfg.C("card2")))

    def _event_item(self, parent, event: dict):
        item = tk.Frame(parent, bg=cfg.C("card2"), padx=10, pady=6, cursor="hand2")
        item.pack(fill="x", pady=2)

        tk.Label(
            item,
            text="📅",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=cfg.C("accent3"),
        ).pack(side="left", padx=(0, 6))

        title_lbl = tk.Label(
            item,
            text=event.get("title", "Untitled"),
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        if event.get("time"):
            tk.Label(
                item,
                text=event["time"],
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card"),
                fg=cfg.C("accent2"),
                padx=6, pady=1,
            ).pack(side="right", padx=(4, 0))

        if event.get("date"):
            tk.Label(
                item,
                text=event["date"],
                font=cfg.FONT["xs"],
                bg=cfg.C("card2"),
                fg=cfg.C("text3"),
            ).pack(side="right", padx=(0, 6))

        def _click(e=None):
            self.hide()
            top = self._anchor.winfo_toplevel()
            EventDialog(
                top,
                on_save=lambda f, eid=event["id"]: self._store.update_event(eid, **f),
                event=event,
            )

        item.bind("<Button-1>", _click)
        title_lbl.bind("<Button-1>", _click)
        item.bind("<Enter>", lambda _: item.configure(bg=cfg.C("border")))
        item.bind("<Leave>", lambda _: item.configure(bg=cfg.C("card2")))
