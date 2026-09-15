"""
OneDesk Card — card.py
Themed card container Frame with optional accent bar and padding.
"""

import tkinter as tk
from .. import config as cfg


class Card(tk.Frame):
    """
    A styled panel card.
    - accent_color: if given, draws a 3px vertical bar on the left.
    - inner_pad: padding inside the card.
    """

    def __init__(self, parent, accent_color=None, inner_pad=cfg.CARD_PAD, **kw):
        outer_bg = kw.pop("bg", cfg.C("card"))
        super().__init__(parent, bg=outer_bg, **kw)

        if accent_color:
            bar = tk.Frame(self, bg=accent_color, width=3)
            bar.pack(side="left", fill="y")

        self.inner = tk.Frame(self, bg=outer_bg, padx=inner_pad, pady=inner_pad)
        self.inner.pack(side="left", fill="both", expand=True)

    # Forward pack/grid/place children into self.inner by default
    def add(self, widget_cls, **kw):
        return widget_cls(self.inner, **kw)
