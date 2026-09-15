# OneDesk — Desktop Productivity App (Tkinter)

A full-featured Python desktop application built with **Tkinter** — a personal productivity dashboard combining notes, tasks, a calendar, and analytics into one sleek, dark-mode native app. All data is stored locally in `~/.onedesk_store.json` — no backend, no internet required.

## Features

- **Auth** — Login, signup, and 1-click demo account (instant sign-in as Alex Rivera)
- **Dashboard** — Greeting banner, KPI stat cards, progress bar, today's schedule, pending tasks, and recent notes
- **Notes** — Grid view with search, category filters, pin/unpin, 5 color labels, tags, edit, delete, export to `.txt`
- **Tasks** — List view + Kanban board (Todo / In Progress / Completed), filter pills, inline quick-add, detailed modal
- **Calendar** — Month, Week, and Day views with event and task-deadline markers; add/edit/delete events
- **Analytics** — Embedded Matplotlib charts: weekly task velocity bar, priority pie, status breakdown bars, notes by category
- **Settings** — Profile editing, Dark/Light theme switcher, JSON backup export & import, clear all data, sign out
- **Global search** — Live search from the top navbar
- **Data seeding** — Fresh install seeds sample notes, tasks, and events so the app isn't empty on first launch

## Tech Stack

- Python 3.13 + Tkinter (stdlib)
- `matplotlib` — embedded charts via TkAgg backend
- `Pillow` — image support (available for future use)

## Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python main.py
```

The window opens at 1280×800. Use **Instant Sign-in** on the login screen for a one-click demo.

## Project Structure

```
onedesk-tkinter/
├── main.py                     # Root Tk window & view router
├── requirements.txt
└── onedesk/
    ├── config.py               # Design tokens (colours, fonts, sizes)
    ├── storage.py              # JSON persistence (~/.onedesk_store.json)
    ├── auth.py                 # User session, demo login, signup
    ├── state.py                # Reactive data store (pub/sub) for Notes/Tasks/Events
    ├── components/
    │   ├── sidebar.py          # Left nav sidebar with active pill
    │   ├── navbar.py           # Top bar: search, quick-add, theme toggle, profile
    │   ├── card.py             # Themed card container
    │   ├── modals.py           # Note / Task / Event dialogs + confirm dialog
    │   └── ui_helpers.py       # Buttons, badges, entries, scrollable frame, tooltip
    └── views/
        ├── auth_view.py        # Login + Signup screen
        ├── dashboard_view.py   # Hero banner, stats, schedule, tasks, recent notes
        ├── notes_view.py       # Notes grid, filters, pin, export
        ├── tasks_view.py       # List + Kanban board
        ├── calendar_view.py    # Month / Week / Day calendar
        ├── analytics_view.py   # Matplotlib embedded charts
        └── settings_view.py    # Profile, theme, backup, sign out
```

## Data Storage

All data lives in `~/.onedesk_store.json`. Use **Export Backup** in Settings to save a JSON snapshot, and **Import Backup** to restore it on any machine.

## Notes

- A fresh install seeds sample data (3 notes, 5 tasks, 4 events) so the dashboard is never empty on first look.
- Theme (dark/light) preference is persisted to the store file automatically.
- The demo account (`alex@lifeos.workspace`) bypasses authentication for instant preview.
