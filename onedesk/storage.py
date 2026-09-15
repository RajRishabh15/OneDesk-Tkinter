"""
OneDesk Storage — storage.py
JSON-based persistence layer, sample data generator, backup export/import.
"""

import json
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

_STORE_FILE = Path(os.path.expanduser("~")) / ".onedesk_store.json"
_PREFIX = "lifeos:"

def _iso(offset_days: int = 0) -> str:
    return (date.today() + timedelta(days=offset_days)).isoformat()


# ── Low-level read/write ─────────────────────────────────────────────────────

def _load_all() -> dict:
    try:
        if _STORE_FILE.exists():
            with open(_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_all(data: dict) -> None:
    try:
        with open(_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_data(key: str, fallback=None):
    return _load_all().get(_PREFIX + key, fallback)


def save_data(key: str, value) -> bool:
    data = _load_all()
    data[_PREFIX + key] = value
    _save_all(data)
    return True


def remove_data(key: str) -> None:
    data = _load_all()
    data.pop(_PREFIX + key, None)
    _save_all(data)


def clear_all_data() -> None:
    data = _load_all()
    keys = [k for k in data if k.startswith(_PREFIX)]
    for k in keys:
        del data[k]
    _save_all(data)


def export_backup() -> dict:
    data = _load_all()
    return {k[len(_PREFIX):]: v for k, v in data.items() if k.startswith(_PREFIX)}


def import_backup(backup: dict) -> None:
    for key, value in backup.items():
        save_data(key, value)


# ── Storage key constants ────────────────────────────────────────────────────

class KEYS:
    USER   = "user"
    USERS  = "users"
    NOTES  = "notes"
    TASKS  = "tasks"
    EVENTS = "events"
    THEME  = "theme"
    SEEDED = "seeded"


# ── Sample data ──────────────────────────────────────────────────────────────

def make_sample_notes():
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "Machine Learning Notes",
            "description": "Topics:\n- Regression\n- Neural Networks\n- Gradient Descent\n\nRevisit backprop derivation before the quiz.",
            "category": "College",
            "tags": ["AI", "College"],
            "color": "violet",
            "pinned": True,
            "createdAt": _iso(0),
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Q3 Product Roadmap",
            "description": "Themes:\n- Onboarding revamp\n- Mobile performance\n- Analytics v2\n\nSync with design on Thursday.",
            "category": "Work",
            "tags": ["Work", "Planning"],
            "color": "cyan",
            "pinned": False,
            "createdAt": _iso(-1),
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Book List — Autumn",
            "description": "- Deep Work\n- The Pragmatic Programmer\n- Atomic Habits (reread)",
            "category": "Personal",
            "tags": ["Reading"],
            "color": "green",
            "pinned": False,
            "createdAt": _iso(-3),
        },
    ]


def make_sample_tasks():
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "Complete OS Assignment",
            "description": "Finish the scheduling algorithm section and write test cases.",
            "priority": "High",
            "dueDate": _iso(1),
            "category": "College",
            "status": "Todo",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Project Meeting Prep",
            "description": "Prepare slides summarising sprint progress.",
            "priority": "Medium",
            "dueDate": _iso(0),
            "category": "Work",
            "status": "In Progress",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Grocery Run",
            "description": "Milk, eggs, coffee, vegetables.",
            "priority": "Low",
            "dueDate": _iso(0),
            "category": "Personal",
            "status": "Todo",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Review PR #482",
            "description": "Check the new auth middleware changes.",
            "priority": "Medium",
            "dueDate": _iso(-1),
            "category": "Work",
            "status": "Completed",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Read Chapter 4 — Deep Work",
            "description": "",
            "priority": "Low",
            "dueDate": _iso(2),
            "category": "Personal",
            "status": "Completed",
        },
    ]


def make_sample_events():
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "OS Lab",
            "date": _iso(0),
            "time": "09:00",
            "description": "Bring lab notebook and pendrive.",
            "reminder": True,
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Project Meeting",
            "date": _iso(0),
            "time": "14:00",
            "description": "Sprint review with the team.",
            "reminder": True,
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Dentist Appointment",
            "date": _iso(2),
            "time": "11:30",
            "description": "",
            "reminder": False,
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Design Sync",
            "date": _iso(4),
            "time": "16:00",
            "description": "Discuss onboarding revamp mockups.",
            "reminder": True,
        },
    ]
