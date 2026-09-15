# LifeOS — Personal Productivity Dashboard

A full-stack-style productivity dashboard combining notes, tasks, a calendar, and analytics into one cohesive app. Built with React, Vite, Tailwind CSS, and plain JavaScript. All data lives in the browser via `localStorage` — there's no backend to run.

## Features

- **Auth UI** — signup/login backed by localStorage, profile settings, logout
- **Dashboard** — greeting, stat cards, today's schedule, recent notes, pending tasks
- **Notes** — create/edit/delete/pin, category filters, search, color labels, markdown-style text, export to `.txt`
- **Tasks** — list view and drag-and-drop kanban board, priority, due dates, category, progress bar
- **Calendar** — month, week, and day views; task deadlines appear automatically alongside events
- **Analytics** — bar chart, pie chart, and progress bars via Recharts
- **Settings** — light/dark theme, notification toggle, JSON backup export/import, clear-all-data
- **Global search** — searches notes, tasks, and events at once from the navbar
- **Keyboard shortcuts** — press `g` then a letter (`d` dashboard, `n` notes, `t` tasks, `c` calendar, `a` analytics, `s` settings)
- Responsive layout with a collapsible mobile sidebar, empty states, and light/dark glassmorphism styling throughout

## Tech stack

- React 19 + Vite
- Tailwind CSS v4 (via `@tailwindcss/vite`)
- react-router-dom for routing
- recharts for charts
- lucide-react for icons

## Getting started

```bash
npm install
npm run dev
```

Then open the printed local URL (typically `http://localhost:5173`). Create an account on the signup screen — everything is stored locally in your browser, so there's nothing to configure.

To build for production:

```bash
npm run build
npm run preview   # optional: preview the production build locally
```

## Project structure

```
src/
  components/     Sidebar, Navbar, Card, Modal, TaskCard, NoteCard, EmptyState, AppLayout, ProtectedRoute
  pages/          Dashboard, Notes, Tasks, Calendar, Analytics, Settings, Login, Signup
  context/        AuthContext, ThemeContext, DataContext
  utils/          storage.js (localStorage helpers), sampleData.js (first-run demo content)
```

## Notes on the data model

- A fresh install seeds a few sample notes, tasks, and events so the dashboard isn't empty on first look. Once you edit or clear that data, the seed never reappears.
- "Import backup" expects a JSON file previously produced by "Export backup" on the Settings page.
- Data currently isn't scoped per account — it's a single shared local dataset, which keeps the demo simple. If you want per-user data, namespace the storage keys in `utils/storage.js` by the logged-in user's id.
