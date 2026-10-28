"""
OneDesk AI Actions — ai_actions.py
Validates and executes structured AI-planned actions through OneDesk DataStore.
Ensures strong validation, error handling, and transactional-style safety.
"""

from datetime import date
from typing import Any


ALLOWED_ACTIONS = {"add_note", "add_task", "add_event"}


def execute_action(store, action: dict) -> dict:
    """
    Executes a single validated action on the provided DataStore.
    Returns:
        {
            "success": True/False,
            "type": action_type,
            "title": action_title,
            "message": "...",
            "item": created_record_dict_or_None
        }
    """
    kind = action.get("type", "")
    if kind not in ALLOWED_ACTIONS:
        return {
            "success": False,
            "type": kind,
            "title": action.get("title", "Unknown"),
            "message": f"Unsupported action type: '{kind}'",
            "item": None,
        }

    raw_title = action.get("title", "")
    title = str(raw_title).strip()
    if not title:
        title = "Untitled Activity"

    today_iso = date.today().isoformat()

    try:
        if kind == "add_note":
            note = store.add_note(
                title=title,
                description=str(action.get("description", "")).strip(),
                category=str(action.get("category", "General") or "General"),
                tags=action.get("tags") if isinstance(action.get("tags"), list) else [],
                color=str(action.get("color", "violet") or "violet"),
                pinned=bool(action.get("pinned", False)),
            )
            return {
                "success": True,
                "type": kind,
                "title": title,
                "message": f"Created note: \"{title}\"",
                "item": note,
            }

        elif kind == "add_task":
            prio = str(action.get("priority", "Medium")).capitalize()
            if prio not in ("High", "Medium", "Low"):
                prio = "Medium"

            status = str(action.get("status", "Todo")).title()
            if status not in ("Todo", "In Progress", "Completed"):
                status = "Todo"

            due_date = str(action.get("dueDate", today_iso)).strip() or today_iso

            task = store.add_task(
                title=title,
                description=str(action.get("description", "")).strip(),
                priority=prio,
                dueDate=due_date,
                status=status,
                category=str(action.get("category", "General") or "General"),
            )
            return {
                "success": True,
                "type": kind,
                "title": title,
                "message": f"Created task: \"{title}\" ({prio} Priority, Due {due_date})",
                "item": task,
            }

        elif kind == "add_event":
            event_date = str(action.get("date", today_iso)).strip() or today_iso
            event_time = str(action.get("time", "10:00")).strip() or "10:00"

            event = store.add_event(
                title=title,
                date=event_date,
                time=event_time,
                reminder=bool(action.get("reminder", True)),
                description=str(action.get("description", "")).strip(),
            )
            return {
                "success": True,
                "type": kind,
                "title": title,
                "message": f"Scheduled event: \"{title}\" on {event_date} at {event_time}",
                "item": event,
            }

    except Exception as e:
        return {
            "success": False,
            "type": kind,
            "title": title,
            "message": f"Execution error: {e}",
            "item": None,
        }

    return {"success": False, "type": kind, "title": title, "message": "Unhandled state", "item": None}


def execute_actions(store, actions: list[dict]) -> tuple[int, list[dict]]:
    """
    Executes a sequence of actions on DataStore.
    Returns (successful_count, list_of_result_dicts).
    """
    results = []
    success_count = 0

    for action in actions:
        res = execute_action(store, action)
        results.append(res)
        if res.get("success"):
            success_count += 1

    return success_count, results
