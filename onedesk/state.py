"""MySQL-backed Notes, Tasks, and Events state with the existing UI API."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
import json
import uuid
from typing import Callable, Iterator

from . import db
from .storage import (
    KEYS,
    export_backup,
    load_data,
    make_sample_events,
    make_sample_notes,
    make_sample_tasks,
    remove_data,
    save_data,
)
from .time_utils import format_time_12h, time_sort_key


_DEFAULT_CATEGORY = "General"
_NOTE_COLORS = {"violet", "cyan", "green", "amber", "rose"}
_TASK_PRIORITIES = {"High", "Medium", "Low"}
_TASK_STATUSES = {"Todo", "In Progress", "Completed"}


def _tag_names(values) -> list[str]:
    if not isinstance(values, list):
        return []
    names = []
    seen = set()
    for value in values:
        if value is None:
            continue
        name = str(value).strip()
        if name and name.casefold() not in seen:
            names.append(name)
            seen.add(name.casefold())
    return names


class PersistenceError(RuntimeError):
    """Safe-to-display error raised when a MySQL persistence operation fails."""


def _date_value(value, *, default=None):
    if value in (None, ""):
        return default
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except (TypeError, ValueError):
        return default


def _datetime_value(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if value:
        try:
            return datetime.fromisoformat(str(value).strip())
        except ValueError:
            pass
    return datetime.now().replace(microsecond=0)


def _date_string(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    parsed = _date_value(value)
    return parsed.isoformat() if parsed else ""


def _time_value(value, default="10:00") -> time:
    value = str(value or "").strip() or default
    for pattern in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(value, pattern).time()
        except ValueError:
            continue
    raise ValueError("Event time must be in HH:MM or HH:MM AM/PM format.")


def _migration_time_value(value) -> time:
    try:
        return _time_value(value)
    except (TypeError, ValueError):
        return _time_value("10:00")


def _time_string(value) -> str:
    if isinstance(value, time):
        return value.strftime("%I:%M %p")
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds()) % (24 * 60 * 60)
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return time(hours, minutes).strftime("%I:%M %p")
    value = str(value or "")
    for pattern in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
        try:
            return datetime.strptime(value, pattern).strftime("%I:%M %p")
        except ValueError:
            continue
    return format_time_12h(value)


def _safe_uuid(value, user_id: str, kind: str, index: int) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        payload = json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
        return str(uuid.uuid5(uuid.UUID(user_id), f"legacy:{kind}:{index}:{payload}"))


def _category_name(value) -> str:
    if not isinstance(value, str):
        return _DEFAULT_CATEGORY
    name = value.strip()
    if not name:
        return _DEFAULT_CATEGORY
    return name if name and len(name) <= 100 else _DEFAULT_CATEGORY


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    return bool(value)


def _legacy_marker() -> dict:
    value = load_data(KEYS.MIGRATED_USERS, {})
    return value if isinstance(value, dict) else {}


class DataStore:
    def __init__(self, user_id: str | None = None):
        self._listeners: list[Callable] = []
        self._user_id: str | None = None
        self.notes: list[dict] = []
        self.tasks: list[dict] = []
        self.events: list[dict] = []
        if user_id:
            self.set_user(user_id)

    @property
    def user_id(self) -> str | None:
        return self._user_id

    def subscribe(self, cb: Callable) -> None:
        if cb not in self._listeners:
            self._listeners.append(cb)

    def unsubscribe(self, cb: Callable) -> None:
        self._listeners = [listener for listener in self._listeners if listener is not cb]

    def _notify(self) -> None:
        for callback in self._listeners:
            try:
                callback()
            except Exception:
                pass

    def _require_user(self) -> str:
        if not self._user_id:
            raise PersistenceError("Sign in before accessing productivity data.")
        return self._user_id

    @contextmanager
    def _transaction(self, action: str) -> Iterator:
        self._require_user()
        try:
            with db.transaction() as conn:
                yield conn
        except PersistenceError:
            raise
        except Exception as exc:
            raise PersistenceError(f"Could not {action}. Check the MySQL connection and try again.") from exc

    def _query(self, sql: str, params=None, action="load productivity data") -> list[dict]:
        self._require_user()
        try:
            return db.query(sql, params or {})
        except Exception as exc:
            raise PersistenceError(f"Could not {action}. Check the MySQL connection and try again.") from exc

    def set_user(self, user_id: str, *, migrate_legacy: bool = False) -> None:
        """Load one authenticated user's data, optionally migrating matched JSON."""
        normalized_id = str(uuid.UUID(str(user_id)))
        self._user_id = normalized_id
        self.notes = self.tasks = self.events = []

        if migrate_legacy:
            self._migrate_legacy_data()
        elif normalized_id == "7cf2f5a8-a36d-4d53-9ce8-ea56ac875b1a":
            marker = _legacy_marker()
            if normalized_id not in marker and not any(
                load_data(key, None) is not None for key in (KEYS.NOTES, KEYS.TASKS, KEYS.EVENTS)
            ):
                # Retain the existing demo-account sample-data experience once.
                counts = self._query(
                    "SELECT (SELECT COUNT(*) FROM notes WHERE user_id=%(user_id)s) AS notes_count, "
                    "(SELECT COUNT(*) FROM tasks WHERE user_id=%(user_id)s) AS tasks_count, "
                    "(SELECT COUNT(*) FROM events WHERE user_id=%(user_id)s) AS events_count",
                    {"user_id": normalized_id},
                )[0]
                if not (counts["notes_count"] or counts["tasks_count"] or counts["events_count"]):
                    self._migrate_records(make_sample_notes(), make_sample_tasks(), make_sample_events())
                marker[normalized_id] = True
                save_data(KEYS.MIGRATED_USERS, marker)

        self._load_from_database()
        self._notify()

    def clear_user(self) -> None:
        """Drop user-specific memory on logout without deleting database data."""
        self._user_id = None
        self.notes = []
        self.tasks = []
        self.events = []
        self._notify()

    def _migrate_legacy_data(self) -> None:
        user_id = self._require_user()
        markers = _legacy_marker()
        if markers.get(user_id):
            for key in (KEYS.NOTES, KEYS.TASKS, KEYS.EVENTS):
                remove_data(key)
            return

        raw_notes = load_data(KEYS.NOTES, [])
        raw_tasks = load_data(KEYS.TASKS, [])
        raw_events = load_data(KEYS.EVENTS, [])
        notes = raw_notes if isinstance(raw_notes, list) else []
        tasks = raw_tasks if isinstance(raw_tasks, list) else []
        events = raw_events if isinstance(raw_events, list) else []

        # Stable generated IDs make retries safe if the DB commit succeeds but
        # writing the local migration marker is interrupted.
        try:
            self._migrate_records(notes, tasks, events)
            markers[user_id] = True
            save_data(KEYS.MIGRATED_USERS, markers)
            for key in (KEYS.NOTES, KEYS.TASKS, KEYS.EVENTS):
                remove_data(key)
        except Exception:
            # Keep the source JSON intact whenever migration/verification fails.
            raise

    def _get_or_create_category(self, conn, kind: str, name: str, cache: dict | None = None) -> str:
        user_id = self._require_user()
        name = _category_name(name)
        cache_key = (kind, name.casefold())
        if cache is not None and cache_key in cache:
            return cache[cache_key]
        category_id = str(uuid.uuid4())
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                "INSERT INTO categories (id,user_id,category_type,name) "
                "VALUES (%(id)s,%(user_id)s,%(category_type)s,%(name)s) "
                "ON DUPLICATE KEY UPDATE id=id",
                {"id": category_id, "user_id": user_id, "category_type": kind, "name": name},
            )
            cur.execute(
                "SELECT id FROM categories WHERE user_id=%(user_id)s AND category_type=%(category_type)s AND name=%(name)s",
                {"user_id": user_id, "category_type": kind, "name": name},
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Category could not be resolved after insert.")
            category_id = str(row["id"])
            if cache is not None:
                cache[cache_key] = category_id
            return category_id
        finally:
            cur.close()

    def _get_or_create_tag(self, conn, name: str, cache: dict | None = None) -> str:
        user_id = self._require_user()
        name = str(name).strip()
        if not name:
            raise ValueError("Tag names cannot be empty.")
        if len(name) > 100:
            raise ValueError("Tag names must be 100 characters or fewer.")
        key = name.casefold()
        if cache is not None and key in cache:
            return cache[key]
        tag_id = str(uuid.uuid4())
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                "INSERT INTO tags (id,user_id,name) VALUES (%(id)s,%(user_id)s,%(name)s) "
                "ON DUPLICATE KEY UPDATE id=id",
                {"id": tag_id, "user_id": user_id, "name": name},
            )
            cur.execute(
                "SELECT id FROM tags WHERE user_id=%(user_id)s AND name=%(name)s",
                {"user_id": user_id, "name": name},
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("Tag could not be resolved after insert.")
            tag_id = str(row["id"])
            if cache is not None:
                cache[key] = tag_id
            return tag_id
        finally:
            cur.close()

    def _record_id(self, conn, table: str, candidate: str, kind: str, index: int) -> str:
        """Normalize an ID; ownership collision checks happen with user-scoped SQL on insert."""
        return _safe_uuid(candidate, self._require_user(), kind, index)

    def _insert_owned_record(self, conn, table: str, record_id: str, candidate,
                             kind: str, index: int, sql: str, values: dict,
                             *, upsert: bool) -> str:
        """Insert idempotently and handle cross-user UUID collisions without reading their rows."""
        user_id = self._require_user()
        suffix = " ON DUPLICATE KEY UPDATE id=id" if upsert else ""
        cur = conn.cursor(dictionary=upsert)
        try:
            if not upsert:
                cur.execute(sql, {**values, "id": record_id})
                return record_id
            for attempt in range(5):
                parameters = {**values, "id": record_id}
                cur.execute(sql + suffix, parameters)
                cur.execute(f"SELECT 1 FROM {table} WHERE id=%(id)s AND user_id=%(user_id)s",
                            {"id": record_id, "user_id": user_id})
                if cur.fetchone() is not None:
                    return record_id
                # A duplicate primary key owned by someone else caused the
                # idempotent insert to do nothing. Allocate a stable private ID.
                record_id = str(uuid.uuid5(uuid.UUID(user_id), f"collision:{kind}:{candidate}:{index}:{attempt}"))
            raise RuntimeError("Could not allocate a safe record identifier.")
        finally:
            cur.close()

    def _write_note(self, conn, note: dict, *, index=0, category_cache=None, tag_cache=None,
                    upsert=False) -> dict:
        user_id = self._require_user()
        category = _category_name(note.get("category"))
        color = str(note.get("color") or "violet").strip().lower()
        if color not in _NOTE_COLORS:
            color = "violet"
        tags = _tag_names(note.get("tags"))
        record_id = self._record_id(conn, "notes", note.get("id"), "note", index)
        category_id = self._get_or_create_category(conn, "note", category, category_cache)
        created_at = _datetime_value(note.get("createdAt"))
        title = str(note.get("title") or "Untitled Note")
        description = str(note.get("description") or "")
        pinned = _as_bool(note.get("pinned", False))
        record_id = self._insert_owned_record(
            conn, "notes", record_id, note.get("id"), "note", index,
            "INSERT INTO notes (id,user_id,category_id,category_type,title,description,color,pinned,created_at) "
            "VALUES (%(id)s,%(user_id)s,%(category_id)s,'note',%(title)s,%(description)s,%(color)s,%(pinned)s,%(created_at)s)",
            {"user_id": user_id, "category_id": category_id, "title": title,
             "description": description, "color": color, "pinned": pinned, "created_at": created_at},
            upsert=upsert,
        )
        cur = conn.cursor()
        try:
            if not upsert:
                cur.execute("DELETE FROM note_tags WHERE note_id=%(id)s AND user_id=%(user_id)s", {"id": record_id, "user_id": user_id})
            for tag_name in tags:
                tag_id = self._get_or_create_tag(conn, tag_name, tag_cache)
                cur.execute(
                    "INSERT IGNORE INTO note_tags (note_id,tag_id,user_id) VALUES (%(note_id)s,%(tag_id)s,%(user_id)s)",
                    {"note_id": record_id, "tag_id": tag_id, "user_id": user_id},
                )
        finally:
            cur.close()
        return {"id": record_id, "title": title, "description": description, "category": category,
                "tags": tags, "color": color, "pinned": pinned, "createdAt": created_at.date().isoformat()}

    def _write_task(self, conn, task: dict, *, index=0, category_cache=None,
                    upsert=False) -> dict:
        user_id = self._require_user()
        category = _category_name(task.get("category"))
        priority = task.get("priority", "Medium")
        priority = priority if isinstance(priority, str) and priority in _TASK_PRIORITIES else "Medium"
        status = task.get("status", "Todo")
        status = status if isinstance(status, str) and status in _TASK_STATUSES else "Todo"
        record_id = self._record_id(conn, "tasks", task.get("id"), "task", index)
        category_id = self._get_or_create_category(conn, "task", category, category_cache)
        due_date = _date_value(task.get("dueDate"))
        completed_at = _date_value(task.get("completedAt")) if status == "Completed" else None
        title = str(task.get("title") or "Untitled")
        description = str(task.get("description") or "")
        record_id = self._insert_owned_record(
            conn, "tasks", record_id, task.get("id"), "task", index,
            "INSERT INTO tasks (id,user_id,category_id,category_type,title,description,priority,status,due_date,completed_at) "
            "VALUES (%(id)s,%(user_id)s,%(category_id)s,'task',%(title)s,%(description)s,%(priority)s,%(status)s,%(due_date)s,%(completed_at)s)",
            {"user_id": user_id, "category_id": category_id, "title": title,
             "description": description, "priority": priority, "status": status,
             "due_date": due_date, "completed_at": completed_at},
            upsert=upsert,
        )
        return {"id": record_id, "title": title, "description": description, "priority": priority,
                "dueDate": due_date.isoformat() if due_date else "", "status": status, "category": category,
                "completedAt": completed_at.isoformat() if completed_at else None}

    def _write_event(self, conn, event: dict, *, index=0, upsert=False) -> dict:
        user_id = self._require_user()
        record_id = self._record_id(conn, "events", event.get("id"), "event", index)
        event_date = _date_value(event.get("date"), default=date.today())
        event_time = _migration_time_value(event.get("time")) if upsert else _time_value(event.get("time", "10:00"))
        title = str(event.get("title") or "Untitled")
        description = str(event.get("description") or "")
        reminder = _as_bool(event.get("reminder", False))
        record_id = self._insert_owned_record(
            conn, "events", record_id, event.get("id"), "event", index,
            "INSERT INTO events (id,user_id,title,event_date,event_time,description,reminder) "
            "VALUES (%(id)s,%(user_id)s,%(title)s,%(event_date)s,%(event_time)s,%(description)s,%(reminder)s)",
            {"user_id": user_id, "title": title, "event_date": event_date,
             "event_time": event_time, "description": description, "reminder": reminder},
            upsert=upsert,
        )
        return {"id": record_id, "title": title, "date": event_date.isoformat(),
                "time": event_time.strftime("%I:%M %p"), "description": description, "reminder": reminder}

    def _migrate_records(self, notes, tasks, events) -> None:
        category_cache, tag_cache = {}, {}
        expected_ids = {"notes": [], "tasks": [], "events": []}
        with self._transaction("migrate local productivity data") as conn:
            for index, note in enumerate(notes):
                if isinstance(note, dict):
                    written = self._write_note(conn, note, index=index, category_cache=category_cache,
                                               tag_cache=tag_cache, upsert=True)
                    expected_ids["notes"].append(written["id"])
            for index, task in enumerate(tasks):
                if isinstance(task, dict):
                    written = self._write_task(conn, task, index=index, category_cache=category_cache, upsert=True)
                    expected_ids["tasks"].append(written["id"])
            for index, event in enumerate(events):
                if isinstance(event, dict):
                    written = self._write_event(conn, event, index=index, upsert=True)
                    expected_ids["events"].append(written["id"])

            # Verify imported rows are visible to this user before committing.
            cur = conn.cursor(dictionary=True)
            try:
                for table, record_ids in expected_ids.items():
                    if record_ids:
                        placeholders = ",".join(["%s"] * len(record_ids))
                        cur.execute(
                            f"SELECT id FROM {table} WHERE user_id=%s AND id IN ({placeholders})",
                            tuple([self._user_id, *record_ids]),
                        )
                        found = {str(row["id"]) for row in cur.fetchall()}
                        if not set(record_ids).issubset(found):
                            raise RuntimeError("Imported records could not be verified.")
            finally:
                cur.close()

    def _load_from_database(self) -> None:
        user_id = self._require_user()
        note_rows = self._query(
            "SELECT n.id,n.title,n.description,c.name AS category,n.color,n.pinned,n.created_at "
            "FROM notes n JOIN categories c ON c.id=n.category_id AND c.user_id=n.user_id "
            "WHERE n.user_id=%(user_id)s ORDER BY n.pinned DESC,n.created_at DESC",
            {"user_id": user_id},
        )
        tag_rows = self._query(
            "SELECT nt.note_id,t.name FROM note_tags nt JOIN tags t ON t.id=nt.tag_id AND t.user_id=nt.user_id "
            "WHERE nt.user_id=%(user_id)s ORDER BY t.name",
            {"user_id": user_id},
        )
        tags_by_note: dict[str, list[str]] = {}
        for row in tag_rows:
            tags_by_note.setdefault(str(row["note_id"]), []).append(row["name"])
        self.notes = [
            {"id": str(row["id"]), "title": row["title"], "description": row["description"] or "",
             "category": row["category"], "tags": tags_by_note.get(str(row["id"]), []), "color": row["color"],
             "pinned": bool(row["pinned"]), "createdAt": _date_string(row["created_at"])}
            for row in note_rows
        ]

        task_rows = self._query(
            "SELECT t.id,t.title,t.description,c.name AS category,t.priority,t.status,t.due_date,t.completed_at "
            "FROM tasks t JOIN categories c ON c.id=t.category_id AND c.user_id=t.user_id "
            "WHERE t.user_id=%(user_id)s ORDER BY t.created_at DESC",
            {"user_id": user_id},
        )
        self.tasks = [
            {"id": str(row["id"]), "title": row["title"], "description": row["description"] or "",
             "category": row["category"], "priority": row["priority"], "status": row["status"],
             "dueDate": _date_string(row["due_date"]),
             "completedAt": _date_string(row["completed_at"]) or None}
            for row in task_rows
        ]

        event_rows = self._query(
            "SELECT id,title,event_date,event_time,description,reminder FROM events "
            "WHERE user_id=%(user_id)s ORDER BY event_date,event_time",
            {"user_id": user_id},
        )
        self.events = [
            {"id": str(row["id"]), "title": row["title"], "date": _date_string(row["event_date"]),
             "time": _time_string(row["event_time"]), "description": row["description"] or "",
             "reminder": bool(row["reminder"])}
            for row in event_rows
        ]

    # Notes
    def add_note(self, **fields) -> dict:
        note = {"id": str(uuid.uuid4()), "createdAt": date.today().isoformat(), "pinned": False, **fields}
        try:
            with self._transaction("save the note") as conn:
                note = self._write_note(conn, note)
        except Exception as exc:
            if isinstance(exc, PersistenceError):
                raise
            raise PersistenceError("Could not save the note. Check the title, category, tags, and MySQL connection.") from exc
        self.notes.insert(0, note)
        self._notify()
        return note

    def update_note(self, note_id: str, **patch) -> None:
        old = next((note for note in self.notes if note["id"] == note_id), None)
        if old is None:
            return
        note = {**old, **patch}
        note["title"] = str(note.get("title") or "Untitled Note")
        note["description"] = str(note.get("description") or "")
        note["category"] = _category_name(note.get("category"))
        note["tags"] = _tag_names(note.get("tags"))
        color = note.get("color")
        note["color"] = color if isinstance(color, str) and color in _NOTE_COLORS else "violet"
        note["pinned"] = _as_bool(note.get("pinned", False))
        try:
            with self._transaction("update the note") as conn:
                category_id = self._get_or_create_category(conn, "note", note.get("category"))
                cur = conn.cursor()
                try:
                    cur.execute(
                        "UPDATE notes SET category_id=%(category_id)s,title=%(title)s,description=%(description)s,"
                        "color=%(color)s,pinned=%(pinned)s WHERE id=%(id)s AND user_id=%(user_id)s",
                        {"category_id": category_id, "title": str(note.get("title") or "Untitled Note"),
                         "description": str(note.get("description") or ""), "color": note.get("color", "violet"),
                         "pinned": _as_bool(note.get("pinned", False)), "id": note_id, "user_id": self._user_id},
                    )
                    if cur.rowcount == 0:
                        return
                    cur.execute("DELETE FROM note_tags WHERE note_id=%(id)s AND user_id=%(user_id)s", {"id": note_id, "user_id": self._user_id})
                finally:
                    cur.close()
                tag_cache = {}
                for tag in note.get("tags", []):
                    tag_id = self._get_or_create_tag(conn, tag, tag_cache)
                    cur = conn.cursor()
                    try:
                        cur.execute("INSERT IGNORE INTO note_tags (note_id,tag_id,user_id) VALUES (%s,%s,%s)", (note_id, tag_id, self._user_id))
                    finally:
                        cur.close()
        except Exception as exc:
            if isinstance(exc, PersistenceError):
                raise
            raise PersistenceError("Could not update the note. Check its fields and the MySQL connection.") from exc
        self.notes = [note if item["id"] == note_id else item for item in self.notes]
        self._notify()

    def delete_note(self, note_id: str) -> None:
        with self._transaction("delete the note") as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM notes WHERE id=%s AND user_id=%s", (note_id, self._user_id))
        self.notes = [note for note in self.notes if note["id"] != note_id]
        self._notify()

    def toggle_pin(self, note_id: str) -> None:
        note = next((item for item in self.notes if item["id"] == note_id), None)
        if note:
            self.update_note(note_id, pinned=not note["pinned"])

    def import_notes(self, notes_list: list[dict]) -> int:
        prepared = []
        for note in notes_list:
            if not isinstance(note, dict):
                continue
            title = str(note.get("title", "")).strip()
            description = str(note.get("description", "")).strip()
            if not title and not description:
                continue
            prepared.append({"id": str(uuid.uuid4()), "title": title or "Untitled Note", "description": description,
                             "category": _category_name(note.get("category")),
                             "tags": note.get("tags") if isinstance(note.get("tags"), list) else [],
                             "color": note.get("color", "violet"), "pinned": _as_bool(note.get("pinned", False)),
                             "createdAt": note.get("createdAt") or date.today().isoformat()})
        if not prepared:
            return 0
        written = []
        with self._transaction("import notes") as conn:
            categories, tags = {}, {}
            for index, note in enumerate(reversed(prepared)):
                written.append(self._write_note(conn, note, index=index, category_cache=categories, tag_cache=tags))
        self._load_from_database()
        self._notify()
        return len(written)

    # Tasks
    def add_task(self, **fields) -> dict:
        task = {"id": str(uuid.uuid4()), "status": "Todo", "completedAt": None, **fields}
        with self._transaction("save the task") as conn:
            task = self._write_task(conn, task)
        self.tasks.insert(0, task)
        self._notify()
        return task

    def update_task(self, task_id: str, **patch) -> None:
        old = next((task for task in self.tasks if task["id"] == task_id), None)
        if old is None:
            return
        task = {**old, **patch}
        category = _category_name(task.get("category"))
        priority = task.get("priority") if isinstance(task.get("priority"), str) and task.get("priority") in _TASK_PRIORITIES else "Medium"
        status = task.get("status") if isinstance(task.get("status"), str) and task.get("status") in _TASK_STATUSES else "Todo"
        due = _date_value(task.get("dueDate"))
        completed = _date_value(task.get("completedAt")) if status == "Completed" else None
        with self._transaction("update the task") as conn:
            category_id = self._get_or_create_category(conn, "task", category)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE tasks SET category_id=%s,title=%s,description=%s,priority=%s,status=%s,due_date=%s,completed_at=%s "
                    "WHERE id=%s AND user_id=%s",
                    (category_id, str(task.get("title") or "Untitled"), str(task.get("description") or ""),
                     priority, status, due, completed, task_id, self._user_id),
                )
        task.update({"category": category, "priority": priority, "status": status,
                     "dueDate": due.isoformat() if due else "", "completedAt": completed.isoformat() if completed else None})
        self.tasks = [task if item["id"] == task_id else item for item in self.tasks]
        self._notify()

    def delete_task(self, task_id: str) -> None:
        with self._transaction("delete the task") as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (task_id, self._user_id))
        self.tasks = [task for task in self.tasks if task["id"] != task_id]
        self._notify()

    def set_task_status(self, task_id: str, status: str) -> None:
        self.update_task(task_id, status=status,
                         completedAt=date.today().isoformat() if status == "Completed" else None)

    def toggle_complete(self, task_id: str) -> None:
        task = next((item for item in self.tasks if item["id"] == task_id), None)
        if task:
            status = "Todo" if task["status"] == "Completed" else "Completed"
            self.set_task_status(task_id, status)

    def import_tasks(self, tasks_list: list[dict]) -> int:
        prepared = []
        for task in tasks_list:
            if not isinstance(task, dict):
                continue
            title = str(task.get("title", "")).strip()
            if not title:
                continue
            priority = task.get("priority", "Medium")
            status = task.get("status", "Todo")
            prepared.append({"id": str(uuid.uuid4()), "title": title,
                             "description": str(task.get("description", "")).strip(),
                             "priority": priority if isinstance(priority, str) and priority in _TASK_PRIORITIES else "Medium",
                             "dueDate": task.get("dueDate") or date.today().isoformat(),
                             "status": status if isinstance(status, str) and status in _TASK_STATUSES else "Todo",
                             "category": _category_name(task.get("category")),
                             "completedAt": task.get("completedAt")})
        if not prepared:
            return 0
        with self._transaction("import tasks") as conn:
            categories = {}
            for index, task in enumerate(reversed(prepared)):
                self._write_task(conn, task, index=index, category_cache=categories)
        self._load_from_database()
        self._notify()
        return len(prepared)

    # Events
    def add_event(self, **fields) -> dict:
        event = {"id": str(uuid.uuid4()), "reminder": False, **fields}
        with self._transaction("save the event") as conn:
            event = self._write_event(conn, event)
        self.events.insert(0, event)
        self._notify()
        return event

    def update_event(self, event_id: str, **patch) -> None:
        old = next((event for event in self.events if event["id"] == event_id), None)
        if old is None:
            return
        event = {**old, **patch}
        event_date = _date_value(event.get("date"), default=date.today())
        try:
            event_time = _time_value(event.get("time", "10:00"))
        except ValueError as exc:
            raise PersistenceError("Event time must use HH:MM or HH:MM AM/PM format.") from exc
        with self._transaction("update the event") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE events SET title=%s,event_date=%s,event_time=%s,description=%s,reminder=%s "
                    "WHERE id=%s AND user_id=%s",
                    (str(event.get("title") or "Untitled"), event_date, event_time,
                     str(event.get("description") or ""), _as_bool(event.get("reminder", False)),
                     event_id, self._user_id),
                )
        event.update({"date": event_date.isoformat(), "time": event_time.strftime("%I:%M %p")})
        self.events = [event if item["id"] == event_id else item for item in self.events]
        self._notify()

    def delete_event(self, event_id: str) -> None:
        with self._transaction("delete the event") as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM events WHERE id=%s AND user_id=%s", (event_id, self._user_id))
        self.events = [event for event in self.events if event["id"] != event_id]
        self._notify()

    def import_events(self, events_list: list[dict]) -> int:
        prepared = []
        for event in events_list:
            if not isinstance(event, dict):
                continue
            title = str(event.get("title", "")).strip()
            if not title:
                continue
            try:
                normalized_time = _time_value(event.get("time") or "10:00").strftime("%H:%M:%S")
            except ValueError:
                normalized_time = "10:00:00"
            prepared.append({"id": str(uuid.uuid4()), "title": title,
                             "date": event.get("date") or date.today().isoformat(),
                             "time": normalized_time, "reminder": _as_bool(event.get("reminder", False)),
                             "description": str(event.get("description", "")).strip()})
        if not prepared:
            return 0
        with self._transaction("import events") as conn:
            for index, event in enumerate(reversed(prepared)):
                self._write_event(conn, event, index=index)
        self._load_from_database()
        self._notify()
        return len(prepared)

    @property
    def completed_tasks(self) -> list[dict]:
        return [task for task in self.tasks if task["status"] == "Completed"]

    @property
    def pending_tasks(self) -> list[dict]:
        return [task for task in self.tasks if task["status"] != "Completed"]

    @property
    def overdue_tasks(self) -> list[dict]:
        today = date.today().isoformat()
        return [task for task in self.tasks if task.get("status") != "Completed" and
                task.get("dueDate") and task["dueDate"] < today]

    @property
    def today_events(self) -> list[dict]:
        today = date.today().isoformat()
        return sorted([event for event in self.events if event.get("date") == today],
                      key=lambda event: time_sort_key(event.get("time", "")))

    @property
    def completion_pct(self) -> int:
        return round(len(self.completed_tasks) / len(self.tasks) * 100) if self.tasks else 0

    def get_backup(self) -> dict:
        self._require_user()
        self._load_from_database()
        backup = export_backup()
        for private_key in (KEYS.USER, KEYS.USERS, KEYS.MIGRATED_USERS, KEYS.LEGACY_DATA_OWNER):
            backup.pop(private_key, None)
        backup.update({"notes": [dict(note) for note in self.notes],
                       "tasks": [dict(task) for task in self.tasks],
                       "events": [dict(event) for event in self.events]})
        return backup

    def restore_backup(self, backup: dict) -> None:
        self._require_user()
        if not isinstance(backup, dict):
            raise PersistenceError("The backup file must contain a JSON object.")
        notes = backup.get(KEYS.NOTES, [])
        tasks = backup.get(KEYS.TASKS, [])
        events = backup.get(KEYS.EVENTS, [])
        notes = notes if isinstance(notes, list) else []
        tasks = tasks if isinstance(tasks, list) else []
        events = events if isinstance(events, list) else []
        try:
            with self._transaction("restore the backup") as conn:
                user_id = self._user_id
                cur = conn.cursor()
                try:
                    cur.execute("DELETE FROM notes WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM tasks WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM events WHERE user_id=%s", (user_id,))
                finally:
                    cur.close()
                categories, tags = {}, {}
                for index, note in enumerate(notes):
                    if isinstance(note, dict):
                        self._write_note(conn, note, index=index, category_cache=categories,
                                         tag_cache=tags, upsert=True)
                for index, task in enumerate(tasks):
                    if isinstance(task, dict):
                        self._write_task(conn, task, index=index, category_cache=categories, upsert=True)
                for index, event in enumerate(events):
                    if isinstance(event, dict):
                        self._write_event(conn, event, index=index, upsert=True)
                # Import local preferences only. A backup must never switch the
                # active account or replace credentials/session identity.
                local_only = {key: value for key, value in backup.items()
                              if key not in {KEYS.NOTES, KEYS.TASKS, KEYS.EVENTS, KEYS.USER, KEYS.USERS,
                                             KEYS.MIGRATED_USERS}}
                from .storage import import_backup
                import_backup(local_only)
        except PersistenceError:
            raise
        except Exception as exc:
            raise PersistenceError("Could not restore the backup. Check the backup data and MySQL connection.") from exc
        self._load_from_database()
        self._notify()

    def clear_all(self) -> None:
        user_id = self._require_user()
        with self._transaction("clear this account's productivity data") as conn:
            cur = conn.cursor()
            try:
                # The order respects category ON DELETE RESTRICT. note_tags
                # cascade from notes; tags/categories remain user-scoped.
                cur.execute("DELETE FROM notes WHERE user_id=%s", (user_id,))
                cur.execute("DELETE FROM tasks WHERE user_id=%s", (user_id,))
                cur.execute("DELETE FROM events WHERE user_id=%s", (user_id,))
                cur.execute("DELETE FROM tags WHERE user_id=%s", (user_id,))
                cur.execute("DELETE FROM categories WHERE user_id=%s", (user_id,))
            finally:
                cur.close()
        self.notes = self.tasks = self.events = []
        self._notify()

    def search(self, query: str) -> dict:
        q = query.lower().strip()
        if not q:
            return {"notes": [], "tasks": [], "events": []}
        return {
            "notes": [note for note in self.notes if q in note.get("title", "").lower() or q in note.get("description", "").lower()],
            "tasks": [task for task in self.tasks if q in task.get("title", "").lower() or q in task.get("description", "").lower()],
            "events": [event for event in self.events if q in event.get("title", "").lower()],
        }
