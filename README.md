# OneDesk — Desktop Productivity App (Tkinter)

A full-featured Python desktop app built with **Tkinter** — a personal productivity dashboard combining notes, tasks, a calendar, and analytics into one sleek native UI. All data is stored locally in `~/.onedesk_store.json` — no backend, no internet required.

---

## Features

- **Auth** — Login, signup, and 1-click **Instant Sign-in** demo (Alex Rivera)
- **Dashboard** — Greeting, 4-stat strip, slim progress bar, pending tasks with quick-complete, today's events, recent notes strip — all minimal and modern
- **Notes** — Grid view with search, category filters, pin/unpin, 5 colour labels, tags, edit, delete, export to `.txt`
- **Tasks** — List view + Kanban board (Todo / In Progress / Completed), filter pills, inline quick-add, detailed modal
- **Calendar** — Month, Week, and Day views with event and task-deadline markers; add/edit/delete events
- **Analytics** — Embedded Matplotlib charts: weekly task velocity bar, priority pie, status breakdown, notes by category
- **Settings** — Profile editing, theme cards (4 themes), JSON backup export & import, clear all data, sign out
- **Global search** — Live search popup from the top navbar with keyboard navigation
- **Collapsible sidebar** — Click the ⬡ logo, "OneDesk" text, or ◀/▶ chevron to toggle between full (210 px) and icon-only (58 px) mode with a smooth slide animation
- **4 themes** — Midnight Purple 🌙, Rose Noir 🌹, Aqua Emerald 🌊, Lavender Light ☀ — cycled from the navbar or chosen in Settings
- **Native title bar** — Windows 10/11 dark-mode title bar via DWM API matches the active theme
- **Data seeding** — Fresh install seeds sample notes, tasks, and events so the dashboard is never empty on first look

---

## Tech Stack

| Layer      | Library            |
|------------|--------------------|
| UI         | Python 3.13 + Tkinter (stdlib) |
| Charts     | `matplotlib` (TkAgg backend) |
| Images     | `Pillow` (available for future use) |
| Persistence| JSON file (`~/.onedesk_store.json`) |
| Platform   | Windows DWM API via `ctypes` |

---

## Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python main.py
```

The window opens at 1280 × 820. Use **Instant Sign-in** on the login screen for a one-click demo.

---

## Project Structure

```
onedesk-tkinter/
├── main.py                     # Root Tk window & view router, theme cycling
├── requirements.txt
└── onedesk/
    ├── config.py               # Design tokens: 4 colour palettes, fonts, sizes, theme helpers
    ├── storage.py              # JSON persistence (~/.onedesk_store.json)
    ├── auth.py                 # User session, demo login, signup
    ├── state.py                # Reactive DataStore (pub/sub) for Notes / Tasks / Events
    ├── platform_helpers.py     # Windows DWM titlebar, DPI awareness, window centering
    ├── components/
    │   ├── sidebar.py          # Collapsible animated sidebar (icon-only ↔ full)
    │   ├── navbar.py           # Top bar: search, quick-add, theme toggle, avatar
    │   ├── search_popup.py     # Live global search overlay with keyboard nav
    │   ├── card.py             # Themed card container
    │   ├── modals.py           # Note / Task / Event dialogs + confirm dialog
    │   └── ui_helpers.py       # Buttons, badges, entries, scrollable frame, separator
    └── views/
        ├── auth_view.py        # Login + Signup screen
        ├── dashboard_view.py   # Minimal dashboard: stats, tasks, events, recent notes
        ├── notes_view.py       # Notes grid, filters, pin, export
        ├── tasks_view.py       # List + Kanban board with search filtering
        ├── calendar_view.py    # Month / Week / Day calendar
        ├── analytics_view.py   # Matplotlib embedded charts
        └── settings_view.py    # Profile, theme cards, backup, sign out
```

---

## Sidebar Collapse

| State     | Width | How to toggle |
|-----------|-------|---------------|
| Expanded  | 210 px | Click ⬡ logo, "OneDesk" text, or **◀** chevron |
| Collapsed | 58 px  | Click ⬡ icon or **▶** chevron; nav icons remain fully clickable |

The animation runs in 10 steps over ~140 ms.

---

## Themes

| Key     | Name            | Icon | Primary colour |
|---------|-----------------|------|----------------|
| `dark`  | Midnight Purple | 🌙   | `#a855f7`      |
| `rose`  | Rose Noir       | 🌹   | `#f43f5e`      |
| `aqua`  | Aqua Emerald    | 🌊   | `#06b6d4`      |
| `light` | Lavender Light  | ☀    | `#7c3aed`      |

Cycle themes via the icon button in the navbar, or pick one in **Settings → Theme**.

---

## Data Storage

All data lives in `~/.onedesk_store.json`. Use **Export Backup** in Settings to save a JSON snapshot, and **Import Backup** to restore it on any machine.

---

## Notes

- A fresh install seeds sample data (3 notes, 5 tasks, 4 events) so the dashboard is never empty.
- Theme preference is persisted automatically.
- The demo account (`alex@lifeos.workspace`) bypasses authentication for instant preview.
- Requires **Windows** for native DWM titlebar styling; the app runs on other platforms but titlebar will be default.

