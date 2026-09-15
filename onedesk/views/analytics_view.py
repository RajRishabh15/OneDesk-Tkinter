"""
OneDesk Analytics View — analytics_view.py
Embedded Matplotlib charts: weekly task velocity, priority distribution,
task status breakdown, and productivity summary metrics.
"""

import tkinter as tk
from datetime import date, timedelta
from .. import config as cfg
from ..components.ui_helpers import make_separator, ScrollableFrame

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


class AnalyticsView(tk.Frame):
    def __init__(self, parent, store, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store = store
        self._figures: list = []
        self._store.subscribe(self._refresh)
        self._build()

    def destroy(self):
        self._store.unsubscribe(self._refresh)
        for fig in self._figures:
            plt.close(fig)
        self._figures.clear()
        super().destroy()

    # ── Build ────────────────────────────────────────────────────────────────
    def _build(self):
        scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        scroll.pack(fill="both", expand=True)
        self._container = scroll.inner
        self._render()

    def _refresh(self):
        for w in self._container.winfo_children():
            w.destroy()
        for fig in self._figures:
            try:
                plt.close(fig)
            except Exception:
                pass
        self._figures.clear()
        self._render()

    def _render(self):
        pad = cfg.PAD
        store = self._store
        tasks = store.tasks
        notes = store.notes

        # ── Page heading ──────────────────────────────────────────────────
        hdr = tk.Frame(self._container, bg=cfg.C("bg"))
        hdr.pack(fill="x", padx=pad, pady=(pad, 4))
        tk.Label(hdr, text="Analytics & Insights", font=cfg.FONT["2xl_b"],
                 bg=cfg.C("bg"), fg=cfg.C("text")).pack(anchor="w")
        tk.Label(hdr, text="Weekly cadence, priority distribution, and productivity velocity.",
                 font=cfg.FONT["sm"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w", pady=(2, 0))

        make_separator(self._container, bg=cfg.C("border")).pack(fill="x", padx=pad, pady=8)

        # ── KPI summary row ───────────────────────────────────────────────
        completed = len(store.completed_tasks)
        total     = len(tasks)
        pct       = store.completion_pct
        notes_wk  = sum(1 for n in notes
                        if (date.today() - date.fromisoformat(n.get("createdAt", "1900-01-01"))).days <= 7
                        if n.get("createdAt", "1900-01-01") > "1900")

        kpi_row = tk.Frame(self._container, bg=cfg.C("bg"))
        kpi_row.pack(fill="x", padx=pad, pady=(0, 12))
        kpi_items = [
            ("🎯", "Productivity Score", f"{pct}%",      cfg.C("accent")),
            ("✅", "Tasks Completed",    str(completed),  cfg.C("success")),
            ("⏳", "Pending Tasks",      str(total - completed), cfg.C("warn")),
            ("📝", "Notes This Week",    str(notes_wk),   cfg.C("accent2")),
        ]
        for i, (icon, title, value, color) in enumerate(kpi_items):
            card = tk.Frame(kpi_row, bg=cfg.C("card"),
                             highlightthickness=1, highlightbackground=cfg.C("border"),
                             padx=18, pady=14)
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            kpi_row.columnconfigure(i, weight=1)
            tk.Label(card, text=icon, font=cfg.FONT["xl"],  bg=cfg.C("card"), fg=color).pack(anchor="w")
            tk.Label(card, text=value, font=cfg.FONT["2xl_b"], bg=cfg.C("card"), fg=cfg.C("text")).pack(anchor="w")
            tk.Label(card, text=title, font=cfg.FONT["xs"],  bg=cfg.C("card"), fg=cfg.C("text2")).pack(anchor="w")

        if not _HAS_MPL:
            tk.Label(self._container, text="⚠️  Install matplotlib for charts: pip install matplotlib",
                     font=cfg.FONT["md"], bg=cfg.C("bg"), fg=cfg.C("warn"), pady=30).pack()
            return

        bg_hex   = cfg.C("bg")
        card_hex = cfg.C("card")
        text_hex = cfg.C("text")
        muted    = cfg.C("text3")

        # ── Chart row: bar + pie ──────────────────────────────────────────
        chart_row = tk.Frame(self._container, bg=cfg.C("bg"))
        chart_row.pack(fill="both", expand=True, padx=pad)
        chart_row.columnconfigure(0, weight=3)
        chart_row.columnconfigure(1, weight=2)

        # Weekly completion bar chart
        days_data = self._weekly_data(tasks)
        fig1, ax1 = plt.subplots(figsize=(5.5, 3))
        self._figures.append(fig1)
        fig1.patch.set_facecolor(card_hex)
        ax1.set_facecolor(card_hex)

        bars = ax1.bar(
            [d["label"] for d in days_data],
            [d["count"] for d in days_data],
            color=cfg.C("accent"), edgecolor="none", width=0.6,
        )
        ax1.set_title("Tasks Completed (Last 7 Days)", color=text_hex, fontsize=9, pad=8)
        ax1.tick_params(colors=muted, labelsize=8)
        for spine in ax1.spines.values():
            spine.set_color(cfg.C("border"))
        ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        fig1.tight_layout(pad=1.5)

        canvas1 = FigureCanvasTkAgg(fig1, master=chart_row)
        canvas1.draw()
        w1 = canvas1.get_tk_widget()
        w1.configure(bg=card_hex)
        w1.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="nsew")

        # Priority pie chart
        priority_data = self._priority_data(tasks)
        labels = [d["name"] for d in priority_data]
        values = [d["value"] for d in priority_data]
        colors = ["#ef4444", "#f59e0b", "#22c55e"]

        fig2, ax2 = plt.subplots(figsize=(3.5, 3))
        self._figures.append(fig2)
        fig2.patch.set_facecolor(card_hex)
        ax2.set_facecolor(card_hex)

        if any(v > 0 for v in values):
            wedges, texts, autotexts = ax2.pie(
                values, labels=labels, colors=colors,
                autopct="%1.0f%%", startangle=90,
                textprops={"color": text_hex, "fontsize": 8},
            )
            for at in autotexts:
                at.set_color(card_hex)
        else:
            ax2.text(0.5, 0.5, "No tasks yet", ha="center", va="center",
                     color=muted, fontsize=9)
        ax2.set_title("By Priority", color=text_hex, fontsize=9, pad=8)
        fig2.tight_layout(pad=1.5)

        canvas2 = FigureCanvasTkAgg(fig2, master=chart_row)
        canvas2.draw()
        w2 = canvas2.get_tk_widget()
        w2.configure(bg=card_hex)
        w2.grid(row=0, column=1, padx=(6, 0), pady=4, sticky="nsew")

        # ── Status breakdown bars ─────────────────────────────────────────
        status_frame = tk.Frame(self._container, bg=cfg.C("card"),
                                 highlightthickness=1, highlightbackground=cfg.C("border"))
        status_frame.pack(fill="x", padx=pad, pady=(8, 12))
        inner = tk.Frame(status_frame, bg=cfg.C("card"), padx=20, pady=16)
        inner.pack(fill="x")
        tk.Label(inner, text="Task Status Breakdown", font=cfg.FONT["md_b"],
                 bg=cfg.C("card"), fg=cfg.C("text")).pack(anchor="w", pady=(0, 10))

        status_colors = {
            "Todo":        cfg.C("text3"),
            "In Progress": cfg.C("accent2"),
            "Completed":   cfg.C("success"),
        }
        for status, color in status_colors.items():
            count = sum(1 for t in tasks if t.get("status") == status)
            ratio = count / total if total else 0

            row = tk.Frame(inner, bg=cfg.C("card"))
            row.pack(fill="x", pady=3)

            tk.Label(row, text=status, font=cfg.FONT["xs_b"], bg=cfg.C("card"),
                     fg=color, width=12, anchor="w").pack(side="left")

            bar_bg = tk.Frame(row, bg=cfg.C("border"), height=10)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(8, 8))
            bar_bg.update_idletasks()
            bar_bg.place_configure()
            # Draw fill lazily using after
            def _draw_bar(bb=bar_bg, r=ratio, c=color):
                bb.update_idletasks()
                w = bb.winfo_width()
                fill_w = int(w * r)
                if fill_w > 0:
                    tk.Frame(bb, bg=c, height=10, width=fill_w).place(x=0, y=0, relheight=1, relwidth=r)
            bar_bg.after(50, _draw_bar)

            tk.Label(row, text=f"{count}", font=cfg.FONT["xs_b"],
                     bg=cfg.C("card"), fg=cfg.C("text2")).pack(side="right")

        # ── Notes-by-category bar (simple matplotlib) ─────────────────────
        cat_data = self._notes_by_category(notes)
        if cat_data:
            fig3, ax3 = plt.subplots(figsize=(9, 2.5))
            self._figures.append(fig3)
            fig3.patch.set_facecolor(card_hex)
            ax3.set_facecolor(card_hex)
            ax3.barh(
                [d["name"] for d in cat_data],
                [d["count"] for d in cat_data],
                color=cfg.C("accent2"), edgecolor="none",
            )
            ax3.set_title("Notes by Category", color=text_hex, fontsize=9, pad=6)
            ax3.tick_params(colors=muted, labelsize=8)
            for spine in ax3.spines.values():
                spine.set_color(cfg.C("border"))
            ax3.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            fig3.tight_layout(pad=1.5)

            canvas3 = FigureCanvasTkAgg(fig3, master=self._container)
            canvas3.draw()
            w3 = canvas3.get_tk_widget()
            w3.configure(bg=card_hex)
            w3.pack(fill="x", padx=pad, pady=(0, pad))

    # ── Data helpers ─────────────────────────────────────────────────────────
    def _weekly_data(self, tasks):
        days = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            iso = d.isoformat()
            count = sum(1 for t in tasks if t.get("status") == "Completed" and t.get("dueDate") == iso)
            days.append({"label": d.strftime("%a"), "count": count})
        return days

    def _priority_data(self, tasks):
        groups = {"High": 0, "Medium": 0, "Low": 0}
        for t in tasks:
            groups[t.get("priority", "Low")] = groups.get(t.get("priority", "Low"), 0) + 1
        return [{"name": k, "value": v} for k, v in groups.items()]

    def _notes_by_category(self, notes):
        cats: dict[str, int] = {}
        for n in notes:
            cat = n.get("category", "General")
            cats[cat] = cats.get(cat, 0) + 1
        return [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])]
