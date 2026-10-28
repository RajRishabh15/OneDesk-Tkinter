"""
OneDesk AI Service — ai_service.py
Google Gemini-powered natural-language action planner and chat assistant.
Interprets multi-action instructions, resolves dates/times, and generates
structured execution plans for Notes, Tasks, and Calendar.
Includes built-in offline NLP fallback when no API key is provided.
"""

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from .storage import load_data, save_data, KEYS

DEFAULT_GEMINI_MODEL = "gemini-flash-latest"


def get_gemini_api_key() -> str:
    """Retrieves the Gemini API key from local storage, env var, or .env file."""
    # 1. Local saved config in OneDesk storage
    saved_key = load_data(KEYS.GEMINI_API_KEY, "")
    if saved_key and str(saved_key).strip():
        return str(saved_key).strip()

    # 2. Environment variables
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # 3. Check for .env file in project root
    try:
        env_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY=") or line.startswith("GOOGLE_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
    except Exception:
        pass

    return ""


def get_gemini_model() -> str:
    """Returns the configured or default Gemini model."""
    saved_model = load_data(KEYS.GEMINI_MODEL, "")
    if saved_model and str(saved_model).strip():
        return str(saved_model).strip()
    return os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def test_gemini_connection(api_key: str, model: str = None) -> tuple[bool, str]:
    """
    Tests connectivity to Google Gemini API using the given key.
    Returns (True, message) on success, or (False, error_details) on failure.
    """
    if not api_key or not api_key.strip():
        return False, "API key cannot be empty."

    model_name = model or get_gemini_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key.strip()}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, respond with OK"}]}],
        "generationConfig": {"maxOutputTokens": 10, "temperature": 0.0},
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True, f"Connected successfully to {model_name}!"
            return False, f"Unexpected response status: {resp.status}"
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            err_msg = err_body.get("error", {}).get("message", str(e))
        except Exception:
            err_msg = str(e)
        return False, f"Gemini API Error: {err_msg}"
    except Exception as e:
        return False, f"Connection failed: {e}"


def plan_actions(user_message: str, current_store_context: dict = None) -> dict:
    """
    Takes natural language input and returns a structured dictionary:
    {
        "message": "Assistant conversational summary",
        "actions": [
            { "type": "add_note"|"add_task"|"add_event", ...params... },
            ...
        ],
        "is_ai": True/False,
        "model": "gemini-1.5-flash" / "offline_nlp"
    }
    """
    api_key = get_gemini_api_key()
    model = get_gemini_model()

    if api_key:
        try:
            return _call_gemini_planner(user_message, api_key, model, current_store_context)
        except Exception as e:
            # Fall back to offline parser with warning if API error occurs
            res = _offline_nlp_planner(user_message)
            res["message"] = f"⚠️ Gemini API was unavailable ({e}). Fallback planner processed your request:\n\n" + res["message"]
            return res
    else:
        # Offline smart rule-based planner
        return _offline_nlp_planner(user_message)


def _call_gemini_planner(user_message: str, api_key: str, model: str, context: dict = None) -> dict:
    now = datetime.now()
    today_str = now.strftime("%A, %B %d, %Y")
    now_iso = now.date().isoformat()
    now_time = now.strftime("%H:%M")

    context_str = ""
    if context:
        tasks_count = context.get("tasks_count", 0)
        notes_count = context.get("notes_count", 0)
        events_count = context.get("events_count", 0)
        context_str = f"Current OneDesk State: {tasks_count} tasks, {notes_count} notes, {events_count} events.\n"

    system_prompt = f"""You are OneDesk AI Assistant, an intelligent personal productivity co-pilot inside OneDesk desktop app.
Current Temporal Anchor:
- Date: {today_str} ({now_iso})
- Current Time: {now_time}
{context_str}

Your goal:
Understand user's natural language and plan concrete actions across Notes, Tasks, and Calendar.
Support single or multiple simultaneous instructions in a single prompt (e.g. "Add a note ..., schedule a meeting ..., and create a task ...").

Action Types and strict schema:
1. "add_note":
   - type: "add_note"
   - title: short clear note title (string)
   - description: note content/body (string)
   - category: "Work" | "Personal" | "College" | "Ideas" | "General" (string)
   - color: "violet" | "cyan" | "green" | "amber" | "rose" (string)
   - pinned: boolean (false by default)

2. "add_task":
   - type: "add_task"
   - title: actionable task name (string)
   - description: optional details (string)
   - priority: "High" | "Medium" | "Low" (string, default "Medium")
   - dueDate: "YYYY-MM-DD" format (calculate relative dates from {now_iso})
   - status: "Todo" | "In Progress" | "Completed" (default "Todo")
   - category: "Work" | "Personal" | "General" | "Focus" (string)

3. "add_event":
   - type: "add_event"
   - title: meeting or event name (string)
   - date: "YYYY-MM-DD" format
   - time: "HH:MM" 24-hour format (e.g. "09:00", "14:30", "21:00")
   - reminder: boolean (default true)
   - description: optional agenda or location details (string)

Rules:
- Calculate relative dates accurately (e.g. "tomorrow", "this Friday", "next Monday", "in 3 days").
- Convert 12-hour AM/PM to 24-hour time (e.g. 9 PM -> "21:00", 10:30 AM -> "10:30").
- If no date is given for a task or event, assume {now_iso}.
- If user asks a general question or greeting, return empty actions list and a helpful message.
- Return ONLY a valid JSON object matching this structure:
{{
  "message": "A friendly, concise summary explaining the actions you prepared or answering the user.",
  "actions": [ ... ]
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{system_prompt}\n\nUser Message: {user_message}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=25) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    raw_text = ""
    candidates = body.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            raw_text = parts[0].get("text", "").strip()

    # Clean markdown fences if model returned ```json ... ```
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

    data = json.loads(raw_text)
    return {
        "message": data.get("message", "I have prepared these actions for you."),
        "actions": data.get("actions", []),
        "is_ai": True,
        "model": model,
    }


def _offline_nlp_planner(user_message: str) -> dict:
    """
    Intelligent offline rule-based action planner.
    Extracts notes, tasks, and calendar events from common natural language phrasing
    when no Gemini API key is configured or when offline.
    """
    msg = user_message.strip()
    actions = []
    now = datetime.now()
    today_iso = now.date().isoformat()
    tomorrow_iso = (now.date() + timedelta(days=1)).isoformat()

    def _extract_time(text: str) -> str:
        # Matches e.g. "9 PM", "9:30 PM", "09:00", "21:00", "at 10 am"
        m = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)\b", text, re.IGNORECASE)
        if m:
            hr = int(m.group(1))
            mn = int(m.group(2) or 0)
            merid = m.group(3).lower().replace(".", "")
            if merid == "pm" and hr < 12:
                hr += 12
            elif merid == "am" and hr == 12:
                hr = 0
            return f"{hr:02d}:{mn:02d}"

        m24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", text)
        if m24:
            return f"{int(m24.group(1)):02d}:{int(m24.group(2)):02d}"
        return "10:00"

    def _extract_date(text: str) -> str:
        lower = text.lower()
        if "tomorrow" in lower:
            return tomorrow_iso
        if "yesterday" in lower:
            return (now.date() - timedelta(days=1)).isoformat()
        # Look for YYYY-MM-DD
        m_iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        if m_iso:
            return m_iso.group(0)
        return today_iso

    # Split message into clauses if user chained instructions with 'and', ',', ';'
    clauses = [c.strip() for c in re.split(r"[,;]|\band\s+(?=(?:add|create|schedule|set|remind|make)\b)", msg, flags=re.IGNORECASE) if c.strip()]
    if not clauses:
        clauses = [msg]

    for clause in clauses:
        c_low = clause.lower().strip()

        # 1. Note Detection (Checked first when user explicitly mentions note/memo)
        if re.search(r"\b(?:add|create|make|write|jot|take)?\s*(?:an?\s+)?(?:note|memo)\b", c_low) or c_low.startswith("note"):
            title = clause
            title = re.sub(r"^(?:add|create|make|write|jot|take)\s+(?:an?\s+)?(?:note|memo)?(?:\s+(?:saying|that|about|for))?\s*", "", title, flags=re.IGNORECASE).strip()
            clean_title = title.strip() or "Quick Note"
            if len(clean_title) > 40:
                short_title = clean_title[:40].rsplit(" ", 1)[0] + "…"
            else:
                short_title = clean_title

            actions.append({
                "type": "add_note",
                "title": short_title.capitalize(),
                "description": clean_title,
                "category": "General",
                "color": "violet",
                "pinned": False,
            })
            continue

        # 2. Calendar Event Detection (Schedule, calendar, meeting, appointment)
        if any(w in c_low for w in ["schedule", "calendar", "meeting", "event", "appointment", "call"]):
            title = clause
            title = re.sub(r"^(?:schedule|add|create|set(?:\s+up)?)\s+(?:an?\s+)?(?:the\s+)?(?:meeting|event|call|appointment)?(?:\s+(?:for|with|called|in\s+my\s+calendar))?\s*", "", title, flags=re.IGNORECASE).strip()
            clean_title = re.sub(r"\s+(?:at|on|for|by|in)\s+.*$", "", title, flags=re.IGNORECASE).strip() or "Scheduled Meeting"
            if clean_title.lower() in ("in my calendar", "the meeting"):
                clean_title = "Meeting"
            event_time = _extract_time(clause)
            event_date = _extract_date(clause)

            actions.append({
                "type": "add_event",
                "title": clean_title.capitalize(),
                "date": event_date,
                "time": event_time,
                "reminder": True,
                "description": f"Created via OneDesk Assistant: {clause}",
            })
            continue

        # 3. Task Detection (task, todo, prepare, finish, complete, buy)
        if any(w in c_low for w in ["task", "todo", "to-do", "prepare", "finish", "complete", "buy", "submit", "reminder", "remind me"]):
            title = clause
            title = re.sub(r"^(?:add|create|set)\s+(?:an?\s+)?(?:task|to-do|todo|reminder)?(?:\s+(?:to|for|about))?\s*", "", title, flags=re.IGNORECASE).strip()
            clean_title = re.sub(r"\s+(?:by|due|at|before)\s+.*$", "", title, flags=re.IGNORECASE).strip() or "New Task"
            prio = "High" if any(w in c_low for w in ["urgent", "asap", "high", "important"]) else "Medium"
            task_date = _extract_date(clause)

            actions.append({
                "type": "add_task",
                "title": clean_title.capitalize(),
                "priority": prio,
                "dueDate": task_date,
                "status": "Todo",
                "category": "Focus",
                "description": f"Created via OneDesk Assistant: {clause}",
            })
            continue

    # If no specific clause matched, create a note or task based on content
    if not actions:
        if len(msg) > 60:
            actions.append({
                "type": "add_note",
                "title": "Quick Thought",
                "description": msg,
                "category": "General",
                "color": "violet",
            })
        else:
            actions.append({
                "type": "add_task",
                "title": msg.capitalize(),
                "priority": "Medium",
                "dueDate": today_iso,
                "status": "Todo",
                "category": "General",
            })

    summary_parts = []
    for a in actions:
        if a["type"] == "add_note":
            summary_parts.append(f"• Note: \"{a['title']}\"")
        elif a["type"] == "add_task":
            summary_parts.append(f"• Task: \"{a['title']}\" (Due: {a.get('dueDate', today_iso)})")
        elif a["type"] == "add_event":
            summary_parts.append(f"• Event: \"{a['title']}\" at {a.get('time', '10:00')} ({a.get('date', today_iso)})")

    actions_list_text = "\n".join(summary_parts)
    message = (
        f"I've parsed your instructions into {len(actions)} action{'s' if len(actions) != 1 else ''}:\n\n"
        f"{actions_list_text}\n\n"
        f"Review the preview cards below and click 'Confirm & Execute' to apply them to your workspace."
    )

    return {
        "message": message,
        "actions": actions,
        "is_ai": False,
        "model": "offline_nlp",
    }
