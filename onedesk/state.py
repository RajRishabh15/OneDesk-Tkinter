"""
OneDesk State — state.py
Centralised reactive data store for Notes, Tasks, and Events.
Supports pub/sub callbacks so views can refresh when data changes.
"""

import uuid
from datetime import date
from typing import Callable
from .storage import (
    load_data, save_data, clear_all_data, export_backup, import_backup,
    make_sample_notes, make_sample_tasks, make_sample_events, KEYS,
)


class DataStore:
    def __init__(self):
        self._listeners: list[Callable] = []

        # Load or seed
        notes  = load_data(KEYS.NOTES,  None)
        tasks  = load_data(KEYS.TASKS,  None)
        events = load_data(KEYS.EVENTS, None)

        self.notes:  list[dict] = notes  if notes  is not None else make_sample_notes()
        self.tasks:  list[dict] = tasks  if tasks  is not None else make_sample_tasks()
        self.events: list[dict] = events if events is not None else make_sample_events()

        self._persist()

    # ── Pub/sub ──────────────────────────────────────────────────────────────
    def subscribe(self, cb: Callable) -> None:
        if cb not in self._listeners:
            self._listeners.append(cb)

    def unsubscribe(self, cb: Callable) -> None:
        self._listeners = [l for l in self._listeners if l is not cb]

    def _notify(self) -> None:
        for cb in self._listeners:
            try:
                cb()
            except Exception:
                pass

    def _persist(self) -> None:
        save_data(KEYS.NOTES,  self.notes)
        save_data(KEYS.TASKS,  self.tasks)
        save_data(KEYS.EVENTS, self.events)

    # ── Notes ────────────────────────────────────────────────────────────────
    def add_note(self, **fields) -> dict:
        note = {
            "id": str(uuid.uuid4()),
            "createdAt": date.today().isoformat(),
            "pinned": False,
            **fields,
        }
        self.notes.insert(0, note)
        self._persist()
        self._notify()
        return note

    def update_note(self, note_id: str, **patch) -> None:
        self.notes = [{**n, **patch} if n["id"] == note_id else n for n in self.notes]
        self._persist()
        self._notify()

    def delete_note(self, note_id: str) -> None:
        self.notes = [n for n in self.notes if n["id"] != note_id]
        self._persist()
        self._notify()

    def toggle_pin(self, note_id: str) -> None:
        self.notes = [
            {**n, "pinned": not n["pinned"]} if n["id"] == note_id else n
            for n in self.notes
        ]
        self._persist()
        self._notify()

    # ── Tasks ────────────────────────────────────────────────────────────────
    def add_task(self, **fields) -> dict:
        task = {
            "id": str(uuid.uuid4()),
            "status": "Todo",
            **fields,
        }
        self.tasks.insert(0, task)
        self._persist()
        self._notify()
        return task

    def update_task(self, task_id: str, **patch) -> None:
        self.tasks = [{**t, **patch} if t["id"] == task_id else t for t in self.tasks]
        self._persist()
        self._notify()

    def delete_task(self, task_id: str) -> None:
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self._persist()
        self._notify()

    def set_task_status(self, task_id: str, status: str) -> None:
        self.update_task(task_id, status=status)

    def toggle_complete(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if task:
            new_status = "Todo" if task["status"] == "Completed" else "Completed"
            self.update_task(task_id, status=new_status)

    # ── Events ───────────────────────────────────────────────────────────────
    def add_event(self, **fields) -> dict:
        event = {
            "id": str(uuid.uuid4()),
            "reminder": False,
            **fields,
        }
        self.events.insert(0, event)
        self._persist()
        self._notify()
        return event

    def update_event(self, event_id: str, **patch) -> None:
        self.events = [{**e, **patch} if e["id"] == event_id else e for e in self.events]
        self._persist()
        self._notify()

    def delete_event(self, event_id: str) -> None:
        self.events = [e for e in self.events if e["id"] != event_id]
        self._persist()
        self._notify()

    # ── Aggregates ───────────────────────────────────────────────────────────
    @property
    def completed_tasks(self) -> list[dict]:
        return [t for t in self.tasks if t["status"] == "Completed"]

    @property
    def pending_tasks(self) -> list[dict]:
        return [t for t in self.tasks if t["status"] != "Completed"]

    @property
    def today_events(self) -> list[dict]:
        today = date.today().isoformat()
        return sorted(
            [e for e in self.events if e.get("date") == today],
            key=lambda e: e.get("time", ""),
        )

    @property
    def completion_pct(self) -> int:
        if not self.tasks:
            return 0
        return round(len(self.completed_tasks) / len(self.tasks) * 100)

    # ── Backup / reset ───────────────────────────────────────────────────────
    def get_backup(self) -> dict:
        return export_backup()

    def restore_backup(self, backup: dict) -> None:
        import_backup(backup)
        notes  = load_data(KEYS.NOTES,  [])
        tasks  = load_data(KEYS.TASKS,  [])
        events = load_data(KEYS.EVENTS, [])
        self.notes  = notes  if isinstance(notes,  list) else []
        self.tasks  = tasks  if isinstance(tasks,  list) else []
        self.events = events if isinstance(events, list) else []
        self._notify()

    def clear_all(self) -> None:
        self.notes  = []
        self.tasks  = []
        self.events = []
        self._persist()
        self._notify()

    # ── Search ───────────────────────────────────────────────────────────────
    def search(self, query: str) -> dict:
        q = query.lower().strip()
        if not q:
            return {"notes": [], "tasks": [], "events": []}
        return {
            "notes":  [n for n in self.notes  if q in n.get("title", "").lower() or q in n.get("description", "").lower()],
            "tasks":  [t for t in self.tasks  if q in t.get("title", "").lower() or q in t.get("description", "").lower()],
            "events": [e for e in self.events if q in e.get("title", "").lower()],
        }
