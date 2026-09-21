"""
OneDesk Notes View — notes_view.py
Notes grid with search, category filters, pin/unpin, color labels, edit, delete, export to .txt.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from .. import config as cfg
from ..components.ui_helpers import (
    make_button, make_separator, ScrollableFrame, make_pill,
)
from ..components.modals import NoteDialog, confirm


class NotesView(tk.Frame):
    def __init__(self, parent, store, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store = store
        self._query = ""
        self._category = "All"

        self._store.subscribe(self._refresh)
        self._build()

    def destroy(self):
        self._store.unsubscribe(self._refresh)
        super().destroy()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        self._top = tk.Frame(self, bg=cfg.C("bg"))
        self._top.pack(fill="x", padx=cfg.PAD, pady=cfg.PAD)
        self._render_top()

        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=cfg.PAD)

        self._scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        self._scroll.pack(fill="both", expand=True, padx=cfg.PAD, pady=(cfg.PAD, 0))
        self._grid_frame = self._scroll.inner
        self._render_notes()

    def _render_top(self):
        for w in self._top.winfo_children():
            w.destroy()

        # Title row
        title_row = tk.Frame(self._top, bg=cfg.C("bg"))
        title_row.pack(fill="x")
        tk.Label(title_row, text="Notes", font=cfg.FONT["2xl_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text")).pack(side="left")
        tk.Label(title_row, text=f"  {len(self._store.notes)} captured",
                 font=cfg.FONT["sm"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(side="left", pady=(6, 0))
        make_button(
            title_row, text="+ New Note",
            command=self._open_new,
            variant="primary",
        ).pack(side="right")

        # Search bar
        search_frame = tk.Frame(self._top, bg=cfg.C("bg"))
        search_frame.pack(fill="x", pady=(10, 6))

        search_outer = tk.Frame(search_frame, bg=cfg.C("card2"),
                                highlightthickness=1, highlightbackground=cfg.C("border"))
        search_outer.pack(side="left", fill="x", expand=True, padx=(0, 12))
        tk.Label(search_outer, text="🔍", font=cfg.FONT["sm"],
                 bg=cfg.C("card2"), fg=cfg.C("text3")).pack(side="left", padx=(8, 4))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        e = tk.Entry(search_outer, textvariable=self._search_var,
                     font=cfg.FONT["sm"], bg=cfg.C("card2"), fg=cfg.C("text"),
                     insertbackground=cfg.C("text"), relief="flat", bd=0)
        e.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))

        # Category filters
        cats_frame = tk.Frame(self._top, bg=cfg.C("bg"))
        cats_frame.pack(fill="x", pady=(0, 4))
        self._cat_btns: list[tk.Button] = []
        cats = ["All"] + sorted({n.get("category", "General") for n in self._store.notes if n.get("category")})
        for cat in cats:
            is_active = cat == self._category
            fg = cfg.C("text") if is_active else cfg.C("text2")
            bg = cfg.C("accent") if is_active else cfg.C("card2")
            btn = tk.Button(
                cats_frame, text=cat, font=cfg.FONT["xs_b"], fg=fg, bg=bg,
                activeforeground=cfg.C("text"), activebackground=cfg.C("accent"),
                relief="flat", bd=0, padx=12, pady=4, cursor="hand2",
                command=lambda c=cat: self._set_category(c),
            )
            btn.pack(side="left", padx=2)
            self._cat_btns.append(btn)

    def _render_notes(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()

        notes = self._filtered_notes()

        if not notes:
            tk.Label(self._grid_frame, text="📝  No notes match your search.",
                     font=cfg.FONT["lg"], bg=cfg.C("bg"), fg=cfg.C("text2"),
                     pady=60).pack(expand=True)
            return

        COLS = 3
        for i, note in enumerate(notes):
            row, col = divmod(i, COLS)
            self._make_note_card(note, row, col)
            self._grid_frame.columnconfigure(col, weight=1)

    def _make_note_card(self, note: dict, row: int, col: int):
        fg, bg = cfg.color_pair(note.get("color", "violet"))
        card = tk.Frame(
            self._grid_frame, bg=bg,
            highlightthickness=1, highlightbackground=fg,
            padx=14, pady=12,
        )
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Pin badge
        top_row = tk.Frame(card, bg=bg)
        top_row.pack(fill="x")
        if note.get("pinned"):
            tk.Label(top_row, text="📌", font=cfg.FONT["xs"], bg=bg, fg=fg).pack(side="right")

        # Title
        tk.Label(card, text=note.get("title", "Untitled"), font=cfg.FONT["md_b"],
                 bg=bg, fg=fg, anchor="w", wraplength=280).pack(anchor="w", pady=(2, 4))

        # Preview
        desc = note.get("description", "")[:140]
        if desc:
            tk.Label(card, text=desc, font=cfg.FONT["xs"], bg=bg, fg=fg,
                     anchor="w", wraplength=280, justify="left").pack(anchor="w", pady=(0, 6))

        # Tags
        if note.get("tags"):
            tags_row = tk.Frame(card, bg=bg)
            tags_row.pack(anchor="w", pady=(0, 6))
            for tag in note["tags"][:3]:
                tk.Label(tags_row, text=f"#{tag}", font=cfg.FONT["xs"],
                         bg=bg, fg=fg, padx=4).pack(side="left")

        # Category + date
        meta_row = tk.Frame(card, bg=bg)
        meta_row.pack(fill="x", pady=(4, 0))
        tk.Label(meta_row, text=note.get("category", ""), font=cfg.FONT["xs"],
                 bg=bg, fg=fg).pack(side="left")
        tk.Label(meta_row, text=note.get("createdAt", "")[:10], font=cfg.FONT["xs"],
                 bg=bg, fg=fg).pack(side="right")

        # Actions row
        actions = tk.Frame(card, bg=bg)
        actions.pack(fill="x", pady=(8, 0))
        for label, cmd in [
            ("Edit",   lambda n=note: self._open_edit(n)),
            ("Pin",    lambda n=note: self._store.toggle_pin(n["id"])),
            ("Export", lambda n=note: self._export_note(n)),
            ("Del",    lambda n=note: confirm(self, f"Delete '{n['title']}'?",
                                               lambda nid=n["id"]: self._store.delete_note(nid))),
        ]:
            tk.Button(
                actions, text=label, font=cfg.FONT["xs_b"], fg=fg, bg=bg,
                activeforeground="#fff", activebackground=cfg.C("accent"),
                relief="flat", bd=0, padx=6, pady=2, cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=2)

    # ── Filtering ────────────────────────────────────────────────────────────
    def _filtered_notes(self):
        notes = self._store.notes
        if self._category != "All":
            notes = [n for n in notes if n.get("category") == self._category]
        if self._query:
            q = self._query.lower()
            notes = [n for n in notes if q in n.get("title", "").lower()
                     or q in n.get("description", "").lower()
                     or any(q in t.lower() for t in n.get("tags", []))]
        return sorted(notes, key=lambda n: (not n.get("pinned", False), ""), reverse=False)

    def _on_search(self, *_):
        self._query = self._search_var.get()
        self._render_notes()

    def _set_category(self, cat: str):
        self._category = cat
        self._render_top()
        self._render_notes()

    def _refresh(self):
        self._render_top()
        self._render_notes()

    # ── Actions ──────────────────────────────────────────────────────────────
    def _open_new(self):
        NoteDialog(self, on_save=self._store.add_note)

    def _open_edit(self, note):
        def _save(fields, nid=note["id"]):
            self._store.update_note(nid, **fields)
        NoteDialog(self, on_save=_save, note=note)

    def _export_note(self, note):
        filename = (note.get("title", "note").replace(" ", "_") or "note") + ".txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=filename,
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return
        content = (
            f"{note.get('title', '')}\n\n"
            f"{note.get('description', '')}\n\n"
            f"Tags: {', '.join(note.get('tags', []))}\n"
            f"Category: {note.get('category', '')}\n"
            f"Created: {note.get('createdAt', '')}\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Exported", f"Note exported to:\n{path}")
