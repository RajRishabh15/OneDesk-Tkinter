"""
OneDesk — main.py
Root Tkinter application. Manages the top-level window, view routing,
theme switching, and ties all components together.
"""

import tkinter as tk
from onedesk import config as cfg
from onedesk.platform_helpers import enable_high_dpi, apply_window_theme, center_window
from onedesk.storage import KEYS, load_data, save_data
from onedesk.auth import AuthManager
from onedesk.state import DataStore
from onedesk.components.sidebar import Sidebar
from onedesk.components.navbar import Navbar
from onedesk.views.auth_view import AuthView
from onedesk.views.dashboard_view import DashboardView
from onedesk.views.notes_view import NotesView
from onedesk.views.tasks_view import TasksView
from onedesk.views.calendar_view import CalendarView
from onedesk.views.analytics_view import AnalyticsView
from onedesk.views.settings_view import SettingsView


VIEW_MAP = {
    "Dashboard": DashboardView,
    "Notes":     NotesView,
    "Tasks":     TasksView,
    "Calendar":  CalendarView,
    "Analytics": AnalyticsView,
    "Settings":  SettingsView,
}


class OneDeskApp:
    def __init__(self):
        # Enable Windows high-DPI awareness before window creation
        enable_high_dpi()

        self._root = tk.Tk()
        self._root.title("OneDesk — Personal Productivity Dashboard")
        self._root.minsize(cfg.MIN_W, cfg.MIN_H)

        # Apply saved theme first
        saved_theme = load_data(KEYS.THEME, "dark")
        cfg.set_theme(saved_theme)
        self._root.configure(bg=cfg.C("bg"))

        # Center window on monitor with comfortable proportions
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        w = min(cfg.WINDOW_W, max(cfg.MIN_W, sw - 80))
        h = min(cfg.WINDOW_H, max(cfg.MIN_H, sh - 100))
        center_window(self._root, w, h)

        # Native Windows 11 / 10 dark title bar styling
        apply_window_theme(self._root, dark=(saved_theme == "dark"))

        # Configure global Tk option database for dark/light mode consistency
        self._root.option_add("*Background", cfg.C("bg"))
        self._root.option_add("*Foreground", cfg.C("text"))
        self._root.option_add("*selectBackground", cfg.C("accent"))
        self._root.option_add("*selectForeground", "#ffffff")
        self._root.option_add("*highlightBackground", cfg.C("border"))
        self._root.option_add("*insertBackground", cfg.C("text"))

        # ── Core state ────────────────────────────────────────────────────
        self._auth  = AuthManager()
        self._store = DataStore()

        # ── Build UI ──────────────────────────────────────────────────────
        self._main_frame  = None  # holds navbar + sidebar + content
        self._auth_frame  = None
        self._content     = None  # current view widget
        self._sidebar_ref = None
        self._navbar_ref  = None
        self._active_view = "Dashboard"

        if self._auth.is_logged_in:
            self._show_main()
        else:
            self._show_auth()

    # ── Auth / main toggle ───────────────────────────────────────────────────
    def _show_auth(self):
        if self._main_frame:
            self._main_frame.destroy()
            self._main_frame = None
        if self._auth_frame:
            self._auth_frame.destroy()

        self._auth_frame = AuthView(
            self._root,
            auth=self._auth,
            on_success=self._on_login,
            bg=cfg.C("bg"),
        )
        self._auth_frame.pack(fill="both", expand=True)

    def _on_login(self):
        if self._auth_frame:
            self._auth_frame.destroy()
            self._auth_frame = None
        self._show_main()

    def _show_main(self):
        if self._auth_frame:
            self._auth_frame.destroy()
            self._auth_frame = None

        self._main_frame = tk.Frame(self._root, bg=cfg.C("bg"))
        self._main_frame.pack(fill="both", expand=True)

        # Navbar (top)
        self._navbar_ref = Navbar(
            self._main_frame,
            store=self._store,
            auth=self._auth,
            on_theme_toggle=self._toggle_theme,
            on_quick_add=self._quick_add_task,
            on_search=self._on_global_search,
        )
        self._navbar_ref.pack(fill="x", side="top")

        # Lower area: sidebar + content
        lower = tk.Frame(self._main_frame, bg=cfg.C("bg"))
        lower.pack(fill="both", expand=True)

        self._sidebar_ref = Sidebar(
            lower,
            on_navigate=self._navigate,
        )
        self._sidebar_ref.pack(side="left", fill="y")

        # Thin separator between sidebar and content
        tk.Frame(lower, bg=cfg.C("border"), width=1).pack(side="left", fill="y")

        self._content_area = tk.Frame(lower, bg=cfg.C("bg"))
        self._content_area.pack(side="left", fill="both", expand=True)

        # Load the default view
        self._navigate(self._active_view)

    # ── Navigation ───────────────────────────────────────────────────────────
    def _navigate(self, view_name: str):
        self._active_view = view_name
        if self._sidebar_ref:
            self._sidebar_ref.set_active(view_name)

        # Destroy existing content
        if self._content:
            self._content.destroy()
            self._content = None

        # Create new view
        view_cls = VIEW_MAP.get(view_name)
        if not view_cls:
            return

        if view_name == "Settings":
            self._content = SettingsView(
                self._content_area,
                store=self._store,
                auth=self._auth,
                on_theme_toggle=self._toggle_theme,
                on_logout=self._on_logout,
                bg=cfg.C("bg"),
            )
        elif view_name == "Analytics":
            self._content = AnalyticsView(
                self._content_area,
                store=self._store,
                bg=cfg.C("bg"),
            )
        elif view_name in ("Dashboard",):
            self._content = DashboardView(
                self._content_area,
                store=self._store,
                auth=self._auth,
                bg=cfg.C("bg"),
            )
        else:
            # Notes, Tasks, Calendar
            self._content = view_cls(
                self._content_area,
                store=self._store,
                bg=cfg.C("bg"),
            )

        self._content.pack(fill="both", expand=True)

    # ── Logout ───────────────────────────────────────────────────────────────
    def _on_logout(self):
        if self._main_frame:
            self._main_frame.destroy()
            self._main_frame = None
        self._content = None
        self._show_auth()

    # ── Theme toggle ─────────────────────────────────────────────────────────
    def _toggle_theme(self, theme_name: str = None):
        new_theme = theme_name if theme_name else cfg.next_theme_name()
        cfg.set_theme(new_theme)
        save_data(KEYS.THEME, new_theme)
        self._root.configure(bg=cfg.C("bg"))

        # Update Windows native titlebar theme
        apply_window_theme(self._root, dark=(new_theme != "light"))

        # Defer rebuild so click event finishes cleanly without TclError
        self._root.after(20, self._rebuild_ui)

    def _rebuild_ui(self):
        if self._auth.is_logged_in:
            active = self._active_view
            if self._main_frame:
                self._main_frame.destroy()
                self._main_frame = None
                self._content = None
                self._sidebar_ref = None
                self._navbar_ref  = None
            self._show_main()
            self._navigate(active)
        else:
            self._show_auth()

    # ── Global search ────────────────────────────────────────────────────────
    def _on_global_search(self, query: str):
        if query:
            self._navigate("Notes")
            if hasattr(self, "_content") and isinstance(self._content, NotesView):
                self._content._search_var.set(query)

    # ── Quick add task from navbar ────────────────────────────────────────────
    def _quick_add_task(self):
        from onedesk.components.modals import TaskDialog
        TaskDialog(self._root, on_save=lambda f: self._store.add_task(**f))

    # ── Run ──────────────────────────────────────────────────────────────────
    def run(self):
        self._root.mainloop()


if __name__ == "__main__":
    app = OneDeskApp()
    app.run()
