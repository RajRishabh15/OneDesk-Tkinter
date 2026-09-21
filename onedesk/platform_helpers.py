"""
OneDesk Platform Helpers — platform_helpers.py
Windows-specific desktop enhancements: High-DPI scaling, DWM dark mode titlebar,
caption/border styling, and window centering.
"""

import sys
import ctypes
import tkinter as tk


def enable_high_dpi():
    """Enable high-DPI scaling on Windows to ensure crisp text and icons."""
    if sys.platform != "win32":
        return
    try:
        # Per-monitor DPI awareness (Windows 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # System DPI awareness fallback (Windows Vista+)
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _hex_to_bgr_int(hex_color: str) -> int:
    """Convert '#RRGGBB' hex color string to Win32 BGR COLORREF integer."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (b << 16) | (g << 8) | r
    return 0


def apply_window_theme(window: tk.Wm, dark: bool = True, caption_hex: str = "", text_hex: str = "", border_hex: str = ""):
    """
    Apply native Windows 10/11 immersive dark mode and optional caption/border colors
    to a Tkinter Tk or Toplevel window.
    """
    if sys.platform != "win32":
        return

    try:
        window.update_idletasks()
        wid = window.winfo_id()
        # Find root HWND
        hwnd = ctypes.windll.user32.GetParent(wid)
        if not hwnd:
            hwnd = wid

        dwmapi = ctypes.windll.dwmapi

        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 11 / Windows 10 20H1+)
        # Fallback to 19 on older Windows 10 builds
        val = ctypes.c_int(1 if dark else 0)
        res = dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        if res != 0:
            dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val), ctypes.sizeof(val))

        # Windows 11 title bar caption & border styling
        # DWMWA_BORDER_COLOR = 34, DWMWA_CAPTION_COLOR = 35, DWMWA_TEXT_COLOR = 36
        if caption_hex:
            c_val = ctypes.c_int(_hex_to_bgr_int(caption_hex))
            dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(c_val), ctypes.sizeof(c_val))
        elif dark:
            # Default rich dark titlebar
            c_val = ctypes.c_int(_hex_to_bgr_int("#19142b"))
            dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(c_val), ctypes.sizeof(c_val))
        else:
            # Light titlebar
            c_val = ctypes.c_int(_hex_to_bgr_int("#ffffff"))
            dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(c_val), ctypes.sizeof(c_val))

        if text_hex:
            t_val = ctypes.c_int(_hex_to_bgr_int(text_hex))
            dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(t_val), ctypes.sizeof(t_val))
        elif dark:
            t_val = ctypes.c_int(_hex_to_bgr_int("#f0eef8"))
            dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(t_val), ctypes.sizeof(t_val))
        else:
            t_val = ctypes.c_int(_hex_to_bgr_int("#1e1b4b"))
            dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(t_val), ctypes.sizeof(t_val))

        if border_hex:
            b_val = ctypes.c_int(_hex_to_bgr_int(border_hex))
            dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(b_val), ctypes.sizeof(b_val))
        elif dark:
            b_val = ctypes.c_int(_hex_to_bgr_int("#2e2749"))
            dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(b_val), ctypes.sizeof(b_val))

    except Exception:
        pass


def center_window(window: tk.Wm, width: int, height: int, parent: tk.Widget = None) -> tuple[int, int]:
    """
    Calculate and apply centered coordinates for a window over its parent or screen.
    Returns (x, y).
    """
    try:
        window.update_idletasks()
    except Exception:
        pass

    if parent is not None:
        try:
            top = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
            top.update_idletasks()
            tw = top.winfo_width()
            th = top.winfo_height()
            tx = top.winfo_rootx()
            ty = top.winfo_rooty()
            if tw > 100 and th > 100:
                x = max(0, tx + (tw - width) // 2)
                y = max(0, ty + (th - height) // 2)
                window.geometry(f"{width}x{height}+{x}+{y}")
                return x, y
        except Exception:
            pass

    # Center over monitor screen
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    return x, y
