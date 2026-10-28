"""
OneDesk Importers — importers.py
Parsers and loaders for importing Notes, Tasks, and Calendar Events
from JSON, CSV, TXT, Markdown, and iCalendar (.ics) files.
"""

import csv
import json
import os
import re
from datetime import date


def _read_file_text(path: str) -> str:
    """Reads file text attempting UTF-8, falling back to Latin-1."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()


# ── Notes Importer ────────────────────────────────────────────────────────────

def parse_notes_file(path: str) -> list[dict]:
    """
    Parses notes from a given file (.json, .csv, .txt, .md).
    Returns a list of dicts with: title, description, category, tags, color, pinned.
    """
    ext = os.path.splitext(path)[1].lower()
    text = _read_file_text(path)

    if ext == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            items = data.get("notes", [data])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        result = []
        for item in items:
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                desc = str(item.get("description", item.get("body", item.get("content", "")))).strip()
                if title or desc:
                    result.append({
                        "title": title or "Untitled Note",
                        "description": desc,
                        "category": item.get("category", "General"),
                        "tags": item.get("tags", []),
                        "color": item.get("color", "violet"),
                        "pinned": bool(item.get("pinned", False)),
                    })
        return result

    elif ext == ".csv":
        result = []
        reader = csv.DictReader(text.splitlines())
        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            title = normalized.get("title", "")
            desc = normalized.get("description") or normalized.get("body") or normalized.get("content", "")
            if title or desc:
                tags_raw = normalized.get("tags", "")
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
                result.append({
                    "title": title or "Untitled Note",
                    "description": desc,
                    "category": normalized.get("category", "General") or "General",
                    "tags": tags,
                    "color": normalized.get("color", "violet") or "violet",
                    "pinned": normalized.get("pinned", "").lower() in ("true", "1", "yes"),
                })
        return result

    elif ext in (".txt", ".md"):
        # Check if file has multiple markdown headers like "# Title" or "## Title"
        header_pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(header_pattern.finditer(text))

        if len(matches) > 1:
            result = []
            for i, match in enumerate(matches):
                title = match.group(2).strip()
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                desc = text[start:end].strip()
                result.append({
                    "title": title,
                    "description": desc,
                    "category": "Notes",
                    "tags": [],
                    "color": "violet",
                    "pinned": False,
                })
            return result
        else:
            # Single note from text/markdown file
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            base_name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
            if not lines:
                return []
            first_line = lines[0].lstrip("#").strip()
            if len(first_line) <= 60 and len(lines) > 1:
                title = first_line
                desc = "\n".join(text.splitlines()[1:]).strip()
            else:
                title = base_name
                desc = text.strip()

            return [{
                "title": title,
                "description": desc,
                "category": "General",
                "tags": [],
                "color": "violet",
                "pinned": False,
            }]

    raise ValueError(f"Unsupported file format: {ext}")


# ── Tasks Importer ────────────────────────────────────────────────────────────

def parse_tasks_file(path: str) -> list[dict]:
    """
    Parses tasks from a given file (.json, .csv, .txt, .md).
    Returns a list of dicts with: title, description, priority, dueDate, status, category.
    """
    ext = os.path.splitext(path)[1].lower()
    text = _read_file_text(path)
    today_iso = date.today().isoformat()

    if ext == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            items = data.get("tasks", [data])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        result = []
        for item in items:
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                if title:
                    prio = item.get("priority", "Medium")
                    if prio not in ("High", "Medium", "Low"):
                        prio = "Medium"
                    status = item.get("status", "Todo")
                    if status not in ("Todo", "In Progress", "Completed"):
                        status = "Todo"
                    result.append({
                        "title": title,
                        "description": str(item.get("description", "")).strip(),
                        "priority": prio,
                        "dueDate": str(item.get("dueDate", item.get("due_date", today_iso))),
                        "status": status,
                        "category": str(item.get("category", "General")),
                    })
        return result

    elif ext == ".csv":
        result = []
        reader = csv.DictReader(text.splitlines())
        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            title = normalized.get("title") or normalized.get("task", "")
            if title:
                prio = normalized.get("priority", "Medium").capitalize()
                if prio not in ("High", "Medium", "Low"):
                    prio = "Medium"
                status = normalized.get("status", "Todo").title()
                if status not in ("Todo", "In Progress", "Completed"):
                    status = "Todo"
                due = normalized.get("duedate") or normalized.get("due_date") or normalized.get("due", today_iso)
                result.append({
                    "title": title,
                    "description": normalized.get("description", ""),
                    "priority": prio,
                    "dueDate": due or today_iso,
                    "status": status,
                    "category": normalized.get("category", "General") or "General",
                })
        return result

    elif ext in (".txt", ".md"):
        # Parse checklist items (- [ ], - [x], or plain bullet lines)
        result = []
        for line in text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            status = "Todo"
            title = line_str

            # Matches - [x] or * [x] or [x]
            m_comp = re.match(r"^[-*]?\s*\[[xX]\]\s*(.+)$", line_str)
            if m_comp:
                status = "Completed"
                title = m_comp.group(1).strip()
            else:
                m_todo = re.match(r"^[-*]?\s*\[\s*\]\s*(.+)$", line_str)
                if m_todo:
                    status = "Todo"
                    title = m_todo.group(1).strip()
                elif re.match(r"^[-*•]\s+(.+)$", line_str):
                    title = re.match(r"^[-*•]\s+(.+)$", line_str).group(1).strip()
                elif re.match(r"^\d+\.\s+(.+)$", line_str):
                    title = re.match(r"^\d+\.\s+(.+)$", line_str).group(1).strip()

            # Priority tag detection like (High) or (Low)
            prio = "Medium"
            m_prio = re.search(r"\((High|Medium|Low)\)", title, re.IGNORECASE)
            if m_prio:
                prio = m_prio.group(1).capitalize()
                title = title.replace(m_prio.group(0), "").strip()

            # Category detection like #Work or #Personal
            cat = "General"
            m_cat = re.search(r"#(\w+)", title)
            if m_cat:
                cat = m_cat.group(1).capitalize()
                title = title.replace(m_cat.group(0), "").strip()

            if title:
                result.append({
                    "title": title,
                    "description": "",
                    "priority": prio,
                    "dueDate": today_iso,
                    "status": status,
                    "category": cat,
                })
        return result

    raise ValueError(f"Unsupported file format: {ext}")


# ── Calendar Events / Activities Importer ─────────────────────────────────────

def parse_events_file(path: str) -> list[dict]:
    """
    Parses calendar events from a given file (.ics, .json, .csv).
    Returns a list of dicts with: title, date, time, reminder, description.
    """
    ext = os.path.splitext(path)[1].lower()
    text = _read_file_text(path)
    today_iso = date.today().isoformat()

    if ext == ".ics":
        # Standard iCalendar parsing (VEVENT blocks)
        events = []
        current = None
        for line in text.splitlines():
            line_clean = line.strip()
            if line_clean == "BEGIN:VEVENT":
                current = {
                    "title": "",
                    "date": today_iso,
                    "time": "10:00",
                    "reminder": False,
                    "description": "",
                }
            elif line_clean == "END:VEVENT":
                if current and current.get("title"):
                    events.append(current)
                current = None
            elif current is not None:
                if ":" in line_clean:
                    key_part, val = line_clean.split(":", 1)
                    key = key_part.split(";")[0].upper()
                    val = val.replace(r"\,", ",").replace(r"\n", "\n").strip()

                    if key == "SUMMARY":
                        current["title"] = val
                    elif key == "DESCRIPTION":
                        current["description"] = val
                    elif key == "LOCATION":
                        if val:
                            if current["description"]:
                                current["description"] += f"\nLocation: {val}"
                            else:
                                current["description"] = f"Location: {val}"
                    elif key == "DTSTART":
                        # Formats: 20261028 or 20261028T143000Z or 20261028T143000
                        val_num = re.sub(r"[^\dT]", "", val)
                        if len(val_num) >= 8:
                            current["date"] = f"{val_num[0:4]}-{val_num[4:6]}-{val_num[6:8]}"
                        if "T" in val_num and len(val_num) >= 13:
                            t_part = val_num.split("T")[1]
                            current["time"] = f"{t_part[0:2]}:{t_part[2:4]}"
        return events

    elif ext == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            items = data.get("events", [data])
        elif isinstance(data, list):
            items = data
        else:
            items = []

        result = []
        for item in items:
            if isinstance(item, dict):
                title = str(item.get("title", "")).strip()
                if title:
                    result.append({
                        "title": title,
                        "date": str(item.get("date", today_iso)),
                        "time": str(item.get("time", "10:00")),
                        "reminder": bool(item.get("reminder", False)),
                        "description": str(item.get("description", "")).strip(),
                    })
        return result

    elif ext == ".csv":
        result = []
        reader = csv.DictReader(text.splitlines())
        for row in reader:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            title = normalized.get("title") or normalized.get("event") or normalized.get("summary", "")
            if title:
                rem = normalized.get("reminder", "").lower() in ("true", "1", "yes")
                result.append({
                    "title": title,
                    "date": normalized.get("date", today_iso) or today_iso,
                    "time": normalized.get("time", "10:00") or "10:00",
                    "reminder": rem,
                    "description": normalized.get("description", ""),
                })
        return result

    raise ValueError(f"Unsupported calendar file format: {ext}")
