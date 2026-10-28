# OneDesk — Desktop Productivity App (Tkinter)

A modern, high-performance personal productivity desktop dashboard built with **Python 3.13** and **Tkinter**. OneDesk brings notes, tasks, calendar events, and account management into a single, cohesive desktop experience with bespoke themes and native Windows title bar integration.

Supports a **hybrid persistence layer**: connect to an optional **MySQL** backend with connection pooling, or run completely offline with automatic zero-configuration **JSON storage**.

---

## Features

### 🔐 Authentication & Onboarding
- **Segmented Auth Mode**: Symmetrical, high-contrast segmented control to switch seamlessly between **Sign In** and **Create Account**.
- **Password Visibility Toggle**: Inline `👁 Show` / `🔒 Hide` button for password masking and unmasking.
- **Top Theme Selector**: Change the application theme directly from the login/signup screen before signing in.
- **Instant Demo Sign-in**: One-click demo login (`Alex Rivera`) seeded with realistic sample data for instant exploration.
- **Security**: Passwords hashed with SHA-256 before storage; parameterised queries protect against SQL injection.

### 📊 Dashboard (Revamped Fluid Design)
- **Fluid Greeting Hero**: Features a circular user profile avatar with ring border, welcoming `"Welcome back, [Name] 👋"` in 22pt bold typography, live date, and contextual time-of-day focus indicator (Morning Focus / Afternoon Momentum / Evening Wrap-up). Clicking the avatar navigates directly to Settings.
- **Inline Quick-Add**: Fluid task input and round `＋` action button right in the header for instantaneous frictionless task creation.
- **6-Metric Stat Strip**: Round icon bubbles and live counts for Tasks, Done, Pending, Notes, Today's Events, plus a Completion Rate gauge with an active animated fill meter. Clicking any metric card instantly navigates to that section.
- **3-Column Workspace**:
  - **Pending Tasks**: Priority pill badges, category & due date metadata, and **dual round action buttons** (`✓` Complete & `✕` Delete) beside each task with hover animations and tooltips.
  - **Today's Schedule**: Event cards with time badges and reminder bells.
  - **Recent Notes**: Fluid colored note chips with category pills and pinned status indicators.
- **Engaging Empty States**: Friendly celebratory icons and quick-create shortcuts when lists are clear.
- **Quick Import Shortcuts**: 1-click round import buttons directly on each column header for rapid ingestion.

### 🤖 AI Personal Assistant (Google Gemini)
- **Natural Language Command Center**: Understands multi-action instructions (e.g. *"Add a note saying I have a meeting at 9 PM, schedule the meeting in my calendar, and add a task to prepare dinner by 10 PM"*).
- **Google Gemini Engine**: Direct REST API integration with `gemini-flash-latest`, `gemini-1.5-flash`, and `gemini-2.0-flash` with zero extra dependencies required. Persistent API key storage in `.env` and local storage.
- **Auto-Wrapping Multi-Line Chat Input**: Responsive auto-expanding text box that expands dynamically up to 6 lines as you type, with keyboard shortcuts (<kbd>Enter</kbd> to submit, <kbd>Shift</kbd>+<kbd>Enter</kbd> for newline).
- **Prompt Editing (`✏️ Edit`)**: One-click edit button on any user message to reload, refine, and re-execute previous prompts effortlessly.
- **Action Edit Modal Dialog (`ActionEditDialog`)**: Inspect and fine-tune planned notes, tasks, or calendar events before execution—modify titles, categories, priorities, due dates, event start/end times, and note bodies.
- **Action Preview & Confirmation Flow**: Previews planned actions as interactive cards with individual confirmation and bulk `"✓ Confirm & Execute All"` buttons.
- **Smart Offline NLP Fallback**: Functions seamlessly even without an API key or when offline using intelligent rule-based parsing.
- **Non-blocking Architecture**: Worker thread offloading ensures the Tkinter desktop UI stays 100% fluid and responsive during network calls.

### 📅 Calendar & Schedule (Modern Grid & Day Drawer)
- **Geometric Uniform Grid**: Strict mathematical cell sizing across all 7 columns and 6 rows (`uniform="cal_col"`, `uniform="cal_row"`), eliminating uneven shapes, layout shifting, and visual clutter.
- **Streamlined Single-Tier Header**: Unified control bar integrating month title, quick-navigation controls (`◀ Today ▶`), segmented view toggle (**Month** | **Week** | **Day**), category filter pills, live search bar, and `+ New Event` button.
- **Slide-Out Day Agenda Drawer**: Clicking any day cell smoothly opens a dedicated right-hand agenda panel showing all activities for that date with color-coded category badges, time ranges, and 1-click event deletion.
- **Multi-View Modes**: Fluid switching between Month grid overview, 7-column time-blocked Week view, and granular Day agenda timeline.
- **High-Contrast Date Badges**: Dynamic date pills highlighting today with the theme accent color, selected date ring indicator, and muted styling for neighboring month overflow days.

### 🎚️ Modern Fluid Scrollbars (macOS & Windows 11 Fluent)
- **Custom Anti-Aliased Pill Thumb**: Built from scratch using a dedicated Tkinter Canvas widget, replacing clunky Windows 95-style bevels, wide troughs, and vintage arrow buttons (`▲`/`▼`).
- **Dynamic Micro-Interactions**: Slim 6px resting profile that smoothly expands to 8px when hovered or dragged.
- **Accent Hover Color Shift**: Thumb color transitions dynamically to the active theme's accent color (`cfg.C("accent")`) on mouse hover and active dragging.
- **Smart Auto-Hiding**: Automatically conceals the scrollbar thumb when content fits within the viewport without overflowing, keeping views clean and distraction-free.
- **Smooth Scrubbing & Track Paging**: Click-to-page track jumps, real-time proportional scrubbing, and cross-platform mouse wheel acceleration.
- **App-wide Coverage**: Embedded across all scrollable views ([DashboardView](file:///r:/onedesk-tkinter/onedesk/views/dashboard_view.py), [NotesView](file:///r:/onedesk-tkinter/onedesk/views/notes_view.py), [TasksView](file:///r:/onedesk-tkinter/onedesk/views/tasks_view.py), [CalendarView](file:///r:/onedesk-tkinter/onedesk/views/calendar_view.py), [AIView](file:///r:/onedesk-tkinter/onedesk/views/ai_view.py), [SettingsView](file:///r:/onedesk-tkinter/onedesk/views/settings_view.py)) via [ScrollableFrame](file:///r:/onedesk-tkinter/onedesk/components/ui_helpers.py#L402-L506).

### 👤 Profile Picture & Account Management
- **Custom Profile Picture**: Upload personal avatar images (PNG, JPG, JPEG, WEBP, BMP, GIF). Images are center-cropped and anti-aliased into high-resolution 256×256 circular portraits, saved to `~/.onedesk/avatars/`.
- **Initials Fallback**: Automatic initials avatar generation with theme accent colors if no custom photo is chosen.
- **Live Sync**: Profile photo updates dynamically reflect in real time across the Navbar chip, Account Dropdown, and Dashboard hero greeting card without needing an app restart.
- **Photo Removal**: One-click photo removal button to revert to default initials avatar anytime.

### 🧭 Navigation & Account Dropdown
- **Collapsible Sidebar**: Clean side navigation focused strictly on workspace views (**Dashboard**, **AI Assistant**, **Notes**, **Tasks**, **Calendar**). Animated toggle (210 px expanded ↔ 58 px icon-only mode) with smooth 10-step width transition.
- **Top Navbar**: Global live search input with autocomplete popup overlay, `＋ Task` shortcut button, active theme dropdown menu, and circular user avatar chip.
- **Account Dropdown**: Clicking the account avatar opens an anchored menu displaying user details (Name, Email, circular avatar preview), direct navigation to **Settings**, and **Log Out**.
- **Settings View**: Accessible via the Account dropdown; manages profile avatar (upload & remove), display name, Google Gemini AI configuration, appearance theme cards, JSON backup export/import, data reset, and sign out.

### 📥 Multi-Format Importers
- **Import Notes**: Ingest notes from **JSON**, **CSV**, **Markdown**, and **Text** files. Supports multi-file selection, automatic markdown header sectioning, tags, and category assignment.
- **Import Tasks**: Ingest tasks from **JSON**, **CSV**, and **Markdown Checklists** (`- [ ]`, `- [x]`, numbered/bullet lists, priority tags like `(High)`, and category hashtags `#Work`).
- **Import Calendar Activities**: Ingest events directly from standard **iCalendar (`.ics`)** files (Google Calendar, Outlook, Apple Calendar), **JSON**, or **CSV** files with automatic date, time, and reminder parsing.
- **Dashboard Quick Import**: 1-click round import buttons directly on each workspace column header on the Dashboard.

### 🎨 Design System & Theming
- **4 Curated Color Themes**:
  - 🌙 **Midnight Purple** (`#a855f7`) — Sleek deep dark mode with purple accents
  - 🌹 **Rose Noir** (`#f43f5e`) — Velvet wine and crimson rose aesthetic
  - 🌊 **Aqua Emerald** (`#06b6d4`) — Oceanic lagoon teal and mint highlights
  - ☀ **Lavender Light** (`#7c3aed`) — Clean, crisp high-contrast light mode
- **Dynamic Component Synchronization**: All widgets, pills, cards, modal dialogs, and custom scrollbars automatically inherit and synchronize with the active theme.
- **Native Windows Title Bar**: Dark mode synchronization using the Windows DWM (Desktop Window Manager) API via `ctypes`.
- **High-DPI Awareness**: Clean font scaling and geometry on Windows 10/11 displays.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.13 | Core runtime and logic |
| **GUI Framework** | Tkinter (Python standard library) | Native cross-platform desktop UI components & custom Canvas widgets |
| **AI Integration** | Google Gemini REST API (`urllib.request`) | Fast natural-language action extraction with zero extra pip dependencies |
| **Database** | MySQL 8.x (`mysql-connector-python`) | Connection pooling, relational storage, and parameterised queries |
| **Fallback Persistence** | JSON (`~/.onedesk_store.json`) | Zero-setup local file storage with automatic fallback |
| **Configuration** | `configparser` (`config.ini`) & `.env` | Database host, credentials, and Gemini API keys |
| **Security** | Python `hashlib` | SHA-256 password hashing |
| **Charts & Visuals** | `matplotlib` (TkAgg backend) | Embedded data plotting and analytics components |
| **Image Handling** | `Pillow` (PIL) | High-DPI avatar circular cropping, masking, and icon asset handling |
| **Platform APIs** | Windows DWM API (`ctypes`) | Windows native title bar theming and DPI awareness |

---

## Project Structure

```
onedesk-tkinter/
├── main.py                     # Application entry point: root window, view routing, lifecycle
├── config.ini                  # MySQL database configuration (host, user, password, database)
├── setup_db.sql                # SQL schema initialization script (users, notes, tasks, events)
├── requirements.txt            # Python dependencies (mysql-connector, matplotlib, Pillow)
├── README.md                   # Project documentation
├── PROJECT_EXPLANATION.md      # Comprehensive deep-dive architecture & component explanation
└── onedesk/
    ├── __init__.py
    ├── config.py               # Design tokens: 4 theme palettes, typography, dimensions
    ├── db.py                   # MySQL connection pool, health check, and query helpers
    ├── auth.py                 # Session manager: MySQL auth with automatic JSON fallback
    ├── state.py                # Reactive DataStore with pub/sub listener architecture
    ├── storage.py              # Local JSON persistence (~/.onedesk_store.json) & sample seeders
    ├── importers.py            # Multi-format parsers for importing Notes, Tasks, and Events
    ├── ai_service.py           # Google Gemini AI action planner & offline smart NLP engine
    ├── ai_actions.py           # Validates and executes planned actions on DataStore
    ├── platform_helpers.py     # Windows DWM titlebar theming, DPI scaling, window centering
    ├── components/
    │   ├── __init__.py
    │   ├── navbar.py           # Header bar: search, +task, theme dropdown, account dropdown
    │   ├── sidebar.py          # Animated collapsible left sidebar (Workspace items)
    │   ├── search_popup.py     # Global live search overlay with keyboard navigation
    │   ├── card.py             # Reusable themed card container
    │   ├── modals.py           # Note, Task, Event dialogs, ActionEditDialog, and confirmation modals
    │   └── ui_helpers.py       # Custom buttons, entries, badges, ModernScrollbar, ScrollableFrame, tooltips
    └── views/
        ├── __init__.py
        ├── auth_view.py        # Login / Signup screen with theme selector & password toggle
        ├── dashboard_view.py   # Overview dashboard with greeting banner, stats strip, 3 columns, task actions
        ├── ai_view.py          # AI Personal Assistant: chat stream, prompt editor, action fine-tuning
        ├── notes_view.py       # Notes grid, color labels, category filtering, search, multi-format export/import
        ├── tasks_view.py       # Task list & Kanban board (Todo / In Progress / Completed) with round actions
        ├── calendar_view.py    # Modern geometric Month grid, 7-column Week view, Day timeline, Agenda drawer
        ├── settings_view.py    # Profile editing, Gemini AI setup, theme cards, backup reset
        └── analytics_view.py   # Embedded Matplotlib charts (available component)
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Windows 10/11 recommended for native title bar styling

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/RajRishabh15/OneDesk-Tkinter.git
cd OneDesk-Tkinter
pip install -r requirements.txt
```

### 3. Launching the App
Run the application:
```bash
python main.py
```

Click **Instant Sign-in →** on the authentication screen to load the demo workspace immediately.

---

## Database Configuration (Optional MySQL)

OneDesk includes dual-storage capability. By default, it operates **offline with local JSON storage** (`~/.onedesk_store.json`). If you wish to use a MySQL database backend:

### Step 1: Set up MySQL Database
Execute the database setup script in MySQL:
```bash
mysql -u root -p < setup_db.sql
```
This creates the `onedesk` database and tables (`users`, `notes`, `tasks`, `events`) with foreign keys and cascading deletes.

### Step 2: Configure Credentials
Edit [`config.ini`](file:///r:/onedesk-tkinter/config.ini) in the project root:
```ini
[mysql]
host     = localhost
port     = 3306
user     = root
password = YOUR_ACTUAL_PASSWORD
database = onedesk
```

### Step 3: Run OneDesk
Start `main.py`. OneDesk automatically tests the database connection via `onedesk/db.py`:
- **If connected**: User accounts and authentication sync with MySQL.
- **If disconnected / offline**: OneDesk seamlessly falls back to the JSON file store without crashing or interrupting the user.

---

## Navigation & Controls

| Element | Interaction | Result |
|---|---|---|
| **Sidebar Collapse** | Click ⬡ logo or ◀ / ▶ chevron | Toggles between 210 px expanded and 58 px icon-only mode (~140 ms animation) |
| **Theme Switcher** | Click **Theme ▾** in Navbar or Auth screen | Opens floating theme picker with preview swatches for all 4 themes |
| **Account Menu** | Click user avatar chip in top navbar | Opens dropdown with user info, **Settings**, and **Log Out** |
| **Global Search** | Click search bar or type query | Displays instant live search overlay across all notes, tasks, and events |
| **Quick Add** | Click **＋ Task** in Navbar or Dashboard | Opens task creation modal from anywhere in the application |
| **Pending Task Actions** | Click `✓` or `✕` on Dashboard/Tasks | Instantly toggles task completion or permanently deletes the task |
| **Calendar Day Click** | Click any day cell in Month view | Slides out the **Day Agenda Drawer** with that date's full chronological event schedule |
| **Fluid Scrollbars** | Hover / Drag / Click track | Smooth 6px→8px expansion, accent color shift, live scrubbing, and page jumping |
| **Edit AI Prompt** | Click `✏️ Edit` on any user chat message | Reloads prompt text into the multi-line input box for instant editing |
| **Edit AI Action** | Click `✏️ Edit` on planned action card | Opens `ActionEditDialog` to adjust title, category, priority, dates, and times |
| **Backup / Restore** | Go to Account → Settings → Data Management | Export all data to JSON or restore an existing backup file |

---

## Keyboard Shortcuts

- <kbd>Enter</kbd> (in AI chat prompt): Submits the prompt to Google Gemini AI
- <kbd>Shift</kbd>+<kbd>Enter</kbd> (in AI chat prompt): Inserts a newline without submitting
- <kbd>Enter</kbd> (in Auth form fields): Advances focus from Name → Email → Password → Submits form
- <kbd>Esc</kbd>: Closes active theme dropdown, account dropdown, or search popup
- <kbd>Enter</kbd> (in Search bar): Navigates directly to the matched item in Notes

