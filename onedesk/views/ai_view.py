"""
OneDesk AI Assistant View — ai_view.py
Interactive AI chat panel powered by Google Gemini:
- Understands multi-action natural language instructions
- Displays action preview cards for Notes, Tasks, and Events
- Confirmation flow: individual execute/dismiss or bulk 'Confirm & Execute All'
- Asynchronous threaded processing preventing Tkinter UI freezing
- Dynamic theme synchronization across all 4 OneDesk color schemes
"""

import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from .. import config as cfg
from ..ai_actions import execute_action, execute_actions
from ..ai_service import (
    get_gemini_api_key, get_gemini_model, plan_actions, test_gemini_connection,
)
from ..components.ui_helpers import (
    make_button, make_pill_badge, make_separator, RoundIconButton, ScrollableFrame,
)
from ..storage import KEYS, load_data, save_data


class AIView(tk.Frame):
    def __init__(self, parent, store, auth=None, on_navigate=None, **kw):
        kw.setdefault("bg", cfg.C("bg"))
        super().__init__(parent, **kw)
        self._store = store
        self._auth = auth
        self._on_navigate = on_navigate
        self._history = []  # list of dicts: {"role": "user"|"ai", "text": "...", "actions": [...], "status": "..."}
        self._is_thinking = False
        self._pending_plan_cards = {}  # plan_id -> widget dict

        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build(self):
        # Header Bar
        self._header = tk.Frame(self, bg=cfg.C("bg"))
        self._header.pack(fill="x", padx=cfg.PAD, pady=(cfg.PAD, 4))
        self._render_header()

        make_separator(self, bg=cfg.C("border")).pack(fill="x", padx=cfg.PAD, pady=(4, 0))

        # Main Chat Scrollable Stream
        self._scroll = ScrollableFrame(self, bg=cfg.C("bg"))
        self._scroll.pack(fill="both", expand=True, padx=cfg.PAD, pady=(8, 0))
        self._chat_container = self._scroll.inner

        # Bottom Input Area
        self._input_frame = tk.Frame(self, bg=cfg.C("card"), highlightthickness=1, highlightbackground=cfg.C("border"))
        self._input_frame.pack(fill="x", side="bottom", padx=cfg.PAD, pady=(8, cfg.PAD))
        self._render_input_bar()

        # Render empty state or history
        self._render_welcome()

    def _render_header(self):
        for w in self._header.winfo_children():
            w.destroy()

        left = tk.Frame(self._header, bg=cfg.C("bg"))
        left.pack(side="left", fill="y")

        title_box = tk.Frame(left, bg=cfg.C("bg"))
        title_box.pack(anchor="w")

        tk.Label(
            title_box,
            text="🤖  AI Assistant",
            font=cfg.FONT["2xl_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(side="left")

        # Engine Status Badge
        api_key = get_gemini_api_key()
        model_name = get_gemini_model()
        if api_key:
            status_text = f"● Google Gemini ({model_name})"
            status_fg = cfg.C("success")
            status_bg = cfg.C("card2")
        else:
            status_text = "● Offline NLP Mode (Add API Key)"
            status_fg = cfg.C("warn")
            status_bg = cfg.C("card2")

        make_pill_badge(
            title_box,
            text=status_text,
            bg=status_bg,
            fg=status_fg,
            font_key="xs_b",
        ).pack(side="left", padx=10)

        tk.Label(
            left,
            text="Natural language command center for your Notes, Tasks, and Calendar.",
            font=cfg.FONT["xs"],
            bg=cfg.C("bg"),
            fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(2, 0))

        # Right Actions
        right = tk.Frame(self._header, bg=cfg.C("bg"))
        right.pack(side="right", anchor="center")

        make_button(
            right,
            text="⚙ Configure Gemini",
            command=self._open_quick_settings,
            variant="secondary",
            font=cfg.FONT["xs_b"],
            padx=10,
            pady=4,
        ).pack(side="left", padx=4)

        make_button(
            right,
            text="🗑 Clear Chat",
            command=self._clear_chat,
            variant="ghost",
            font=cfg.FONT["xs_b"],
            padx=8,
            pady=4,
        ).pack(side="left")

    PLACEHOLDER_TEXT = "Ask OneDesk AI anything or give multi-action commands... (Shift+Enter for newline)"

    def _render_input_bar(self):
        for w in self._input_frame.winfo_children():
            w.destroy()

        self._has_placeholder = True

        self._input_frame.configure(
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
        )

        inner = tk.Frame(self._input_frame, bg=cfg.C("card"), padx=14, pady=10)
        inner.pack(fill="x")

        # ── 1. Top Quick Action / Suggestion Chips ────────────────────────────
        top_bar = tk.Frame(inner, bg=cfg.C("card"))
        top_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            top_bar,
            text="✨ Quick Prompts:",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
        ).pack(side="left", padx=(0, 6))

        suggestions = [
            ("📝 Multi-Action Combo", "Add a note saying meeting at 9 PM, schedule the meeting in my calendar, and add a task to prepare dinner by 10 PM."),
            ("📅 Schedule Meeting", "Schedule project review with design team tomorrow at 2:00 PM."),
            ("✔ Prioritized Task", "Add urgent task: Review client presentation by 5 PM with High priority."),
            ("💡 Brainstorm Note", "Note: Product ideas for mobile dashboard and UX enhancements."),
        ]

        for label, full_prompt in suggestions:
            chip = tk.Button(
                top_bar,
                text=label,
                font=cfg.FONT["xs"],
                bg=cfg.C("card2"),
                fg=cfg.C("text2"),
                activebackground=cfg.C("accent"),
                activeforeground="#ffffff",
                relief="flat",
                bd=0,
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda p=full_prompt: self._use_suggestion(p),
            )
            chip.pack(side="left", padx=3)

            def _hover_enter(e, c=chip):
                c.configure(bg=cfg.C("accent"), fg="#ffffff")
            def _hover_leave(e, c=chip):
                c.configure(bg=cfg.C("card2"), fg=cfg.C("text2"))
            chip.bind("<Enter>", _hover_enter)
            chip.bind("<Leave>", _hover_leave)

        # ── 2. Modern Multi-Line Input Box ────────────────────────────────────
        entry_outer = tk.Frame(
            inner,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=10,
            pady=8,
        )
        entry_outer.pack(fill="x", pady=(0, 8))
        self._entry_outer = entry_outer

        # Magic Sparkle Icon Prefix
        prefix_box = tk.Frame(entry_outer, bg=cfg.C("card2"))
        prefix_box.pack(side="left", anchor="nw", padx=(0, 8), pady=2)
        tk.Label(
            prefix_box,
            text="✨",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("accent"),
        ).pack()

        # Multi-line Text Widget
        self._text_input = tk.Text(
            entry_outer,
            height=2,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            wrap="word",
            padx=2,
            pady=2,
            undo=True,
        )
        self._text_input.pack(side="left", fill="x", expand=True)
        self._text_input.insert("1.0", self.PLACEHOLDER_TEXT)

        # ── 3. Bottom Controls & Status Row ───────────────────────────────────
        controls_row = tk.Frame(inner, bg=cfg.C("card"))
        controls_row.pack(fill="x")

        # Left: Keyboard Shortcuts Legend
        hints_frame = tk.Frame(controls_row, bg=cfg.C("card"))
        hints_frame.pack(side="left", fill="y")

        tk.Label(
            hints_frame,
            text="↵ Enter to send  ·  ⇧+↵ for new line  ·  ↑ to recall previous  ·  Esc to clear",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(side="left")

        # Right: Live Stats & Action Buttons
        right_actions = tk.Frame(controls_row, bg=cfg.C("card"))
        right_actions.pack(side="right")

        # Character Counter
        self._char_counter = tk.Label(
            right_actions,
            text="0 chars",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        )
        self._char_counter.pack(side="left", padx=(0, 10))

        # Clear Button
        self._clear_btn = tk.Button(
            right_actions,
            text="✕ Clear",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text2"),
            activebackground=cfg.C("card"),
            activeforeground=cfg.C("danger"),
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            command=self._clear_input,
        )
        self._clear_btn.pack(side="left", padx=(0, 8))

        # Send Button
        self._send_btn = tk.Button(
            right_actions,
            text="➤ Send",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("accent"),
            fg="#ffffff",
            activebackground=cfg.C("accent2"),
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=14,
            pady=4,
            cursor="hand2",
            command=self._send_message,
        )
        self._send_btn.pack(side="left")

        # Event Handlers
        def _on_focus_in(_):
            entry_outer.configure(highlightbackground=cfg.C("accent"))
            self._input_frame.configure(highlightbackground=cfg.C("accent"))
            if self._has_placeholder:
                self._has_placeholder = False
                self._text_input.delete("1.0", "end")
                self._text_input.configure(fg=cfg.C("text"))

        def _on_focus_out(_):
            entry_outer.configure(highlightbackground=cfg.C("border"))
            self._input_frame.configure(highlightbackground=cfg.C("border"))
            if not self._get_input_text():
                self._show_placeholder()

        def _on_key_press(event):
            # Plain Enter sends message; Shift+Enter creates a new line
            if event.keysym == "Return" and not (event.state & 0x0001):
                self._send_message()
                return "break"
            elif event.keysym == "Up":
                cursor_idx = self._text_input.index("insert")
                if self._has_placeholder or cursor_idx == "1.0":
                    self._recall_previous_prompt()
                    return "break"
            elif event.keysym == "Escape":
                self._clear_input()
                return "break"
            return None

        def _on_key_release(_):
            self._update_input_state()

        self._text_input.bind("<FocusIn>", _on_focus_in)
        self._text_input.bind("<FocusOut>", _on_focus_out)
        self._text_input.bind("<KeyPress>", _on_key_press)
        self._text_input.bind("<KeyRelease>", _on_key_release)

    def _render_welcome(self):
        for w in self._chat_container.winfo_children():
            w.destroy()

        welcome_card = tk.Frame(
            self._chat_container,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=24,
            pady=28,
        )
        welcome_card.pack(fill="x", pady=16)

        # Icon Bubble
        tk.Label(
            welcome_card,
            text="🤖",
            font=(cfg.FONT_FAMILY, 32),
            bg=cfg.C("card"),
        ).pack()

        tk.Label(
            welcome_card,
            text="OneDesk AI Personal Assistant",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
        ).pack(pady=(6, 4))

        tk.Label(
            welcome_card,
            text="Tell me what you'd like to do in plain English. I can simultaneously create notes, schedule calendar meetings, and add prioritized tasks.",
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
            wraplength=640,
            justify="center",
        ).pack(pady=(0, 16))

        # Example Prompts Grid
        grid = tk.Frame(welcome_card, bg=cfg.C("card"))
        grid.pack(pady=4)

        cards = [
            ("📝 Multi-Action Combo", "Add a note saying I have a meeting at 9 PM, schedule the meeting in my calendar, and add a task to prepare dinner by 10 PM."),
            ("📅 Calendar Scheduling", "Schedule design team sync tomorrow from 2:00 PM to 3:00 PM with reminder."),
            ("✔ Task Management", "Add urgent task: Review pull request by 5 PM and task to submit project timesheet."),
            ("💡 Quick Note", "Write down note: Ideas for upcoming mobile dashboard revamp and tag it #UX."),
        ]

        for i, (hdr, prompt_text) in enumerate(cards):
            r, c = divmod(i, 2)
            box = tk.Frame(
                grid,
                bg=cfg.C("card2"),
                highlightthickness=1,
                highlightbackground=cfg.C("border"),
                padx=14,
                pady=12,
                cursor="hand2",
            )
            box.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            grid.columnconfigure(c, weight=1)

            tk.Label(
                box,
                text=hdr,
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card2"),
                fg=cfg.C("accent"),
                anchor="w",
            ).pack(fill="x")

            tk.Label(
                box,
                text=f"\"{prompt_text}\"",
                font=cfg.FONT["xs"],
                bg=cfg.C("card2"),
                fg=cfg.C("text"),
                wraplength=280,
                justify="left",
                anchor="w",
            ).pack(fill="x", pady=(4, 0))

            def _click(t=prompt_text):
                self._use_suggestion(t)

            for w in (box, *box.winfo_children()):
                w.bind("<Button-1>", lambda _, t=prompt_text: _click(t))

    # ── Interaction & Chat Engine ─────────────────────────────────────────────
    def _get_input_text(self) -> str:
        if getattr(self, "_has_placeholder", True) or not hasattr(self, "_text_input"):
            return ""
        return self._text_input.get("1.0", "end-1c").strip()

    def _set_input_text(self, text: str):
        if not hasattr(self, "_text_input"):
            return
        self._has_placeholder = False
        self._text_input.delete("1.0", "end")
        if text:
            self._text_input.configure(fg=cfg.C("text"))
            self._text_input.insert("1.0", text)
        else:
            self._show_placeholder()
        self._update_input_state()

    def _show_placeholder(self):
        if not hasattr(self, "_text_input"):
            return
        self._has_placeholder = True
        self._text_input.delete("1.0", "end")
        self._text_input.insert("1.0", self.PLACEHOLDER_TEXT)
        self._text_input.configure(fg=cfg.C("text3"))
        self._update_input_state()

    def _clear_input(self):
        self._set_input_text("")
        if hasattr(self, "_text_input"):
            self._text_input.focus_set()

    def _update_input_state(self):
        text = self._get_input_text()
        char_len = len(text)
        if hasattr(self, "_char_counter"):
            self._char_counter.configure(text=f"{char_len} chars")

        # Auto-adjust height dynamically between 2 and 4 lines
        if hasattr(self, "_text_input"):
            lines = text.count("\n") + 1
            new_height = max(2, min(4, lines))
            curr_height = int(self._text_input.cget("height"))
            if new_height != curr_height:
                self._text_input.configure(height=new_height)

        # Clear button appearance
        if hasattr(self, "_clear_btn"):
            if text:
                self._clear_btn.configure(fg=cfg.C("text"), state="normal")
            else:
                self._clear_btn.configure(fg=cfg.C("text3"), state="normal")

        # Send button visual cue
        if hasattr(self, "_send_btn") and not self._is_thinking:
            if text:
                self._send_btn.configure(
                    bg=cfg.C("accent"),
                    fg="#ffffff",
                    activebackground=cfg.C("accent2"),
                    state="normal",
                )
            else:
                self._send_btn.configure(
                    bg=cfg.C("card2"),
                    fg=cfg.C("text2"),
                    activebackground=cfg.C("card"),
                    state="normal",
                )

    def _update_send_button_state(self):
        if not hasattr(self, "_send_btn") or not self._send_btn.winfo_exists():
            return
        if self._is_thinking:
            self._send_btn.configure(
                text="⏳ Planning...",
                bg=cfg.C("card2"),
                fg=cfg.C("accent"),
                state="disabled",
            )
        else:
            self._send_btn.configure(
                text="➤ Send",
                bg=cfg.C("accent"),
                fg="#ffffff",
                state="normal",
            )
        self._update_input_state()

    def _recall_previous_prompt(self):
        for item in reversed(self._history):
            if item.get("role") == "user":
                self._edit_user_prompt(item.get("text", ""))
                break

    def _use_suggestion(self, text: str):
        self._set_input_text(text)
        if hasattr(self, "_text_input"):
            self._text_input.focus_set()
            self._text_input.mark_set("insert", "end")

    def _edit_user_prompt(self, text: str):
        self._set_input_text(text)
        if hasattr(self, "_text_input"):
            self._text_input.focus_set()
            self._text_input.tag_add("sel", "1.0", "end")
            self._text_input.mark_set("insert", "end")
        self._scroll_to_bottom()

    def _clear_chat(self):
        self._history = []
        self._render_welcome()

    def _send_message(self):
        if self._is_thinking:
            return

        user_text = self._get_input_text()
        if not user_text:
            return

        self._set_input_text("")

        # Update Send button state to thinking
        self._is_thinking = True
        self._update_send_button_state()

        # Remove welcome card if first message
        if not self._history:
            for w in self._chat_container.winfo_children():
                w.destroy()

        # Append User Bubble
        timestamp = datetime.now().strftime("%I:%M %p")
        self._history.append({"role": "user", "text": user_text, "time": timestamp})
        self._render_user_bubble(user_text, timestamp)

        # Show Loading Indicator
        self._render_thinking_card()

        # Prepare context
        store_context = {
            "tasks_count": len(self._store.tasks),
            "notes_count": len(self._store.notes),
            "events_count": len(self._store.events),
        }

        # Run AI planning in a background thread to prevent UI freezing
        def _worker():
            try:
                res = plan_actions(user_text, current_store_context=store_context)
            except Exception as e:
                res = {
                    "message": f"An error occurred while processing: {e}",
                    "actions": [],
                    "is_ai": False,
                }
            self.after(0, lambda: self._on_ai_response(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _render_user_bubble(self, text: str, timestamp: str):
        wrap = tk.Frame(self._chat_container, bg=cfg.C("bg"))
        wrap.pack(fill="x", pady=6)

        bubble = tk.Frame(
            wrap,
            bg=cfg.C("card2"),
            highlightthickness=1,
            highlightbackground=cfg.C("accent"),
            padx=14,
            pady=10,
        )
        bubble.pack(side="right", anchor="e")

        top = tk.Frame(bubble, bg=cfg.C("card2"))
        top.pack(fill="x")

        tk.Label(
            top,
            text="You",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("accent"),
        ).pack(side="left")

        tk.Label(
            top,
            text=f" · {timestamp}",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=cfg.C("text3"),
        ).pack(side="left")

        # Edit prompt button
        tk.Button(
            top,
            text="✏️ Edit",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("text2"),
            activebackground=cfg.C("card"),
            activeforeground=cfg.C("accent"),
            relief="flat",
            bd=0,
            padx=6,
            pady=0,
            cursor="hand2",
            command=lambda t=text: self._edit_user_prompt(t),
        ).pack(side="right", padx=(8, 0))

        tk.Label(
            bubble,
            text=text,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            wraplength=600,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        self._scroll_to_bottom()

    def _render_thinking_card(self):
        self._thinking_wrap = tk.Frame(self._chat_container, bg=cfg.C("bg"))
        self._thinking_wrap.pack(fill="x", pady=6)

        card = tk.Frame(
            self._thinking_wrap,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=14,
            pady=10,
        )
        card.pack(side="left", anchor="w")

        tk.Label(
            card,
            text="🤖  OneDesk AI is thinking & planning actions…",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent"),
        ).pack(side="left", padx=4)

        self._scroll_to_bottom()

    def _on_ai_response(self, plan: dict):
        self._is_thinking = False
        self._update_send_button_state()
        if hasattr(self, "_thinking_wrap") and self._thinking_wrap.winfo_exists():
            self._thinking_wrap.destroy()

        timestamp = datetime.now().strftime("%I:%M %p")
        message = plan.get("message", "Here is what I prepared.")
        actions = plan.get("actions", [])
        is_ai = plan.get("is_ai", False)
        model = plan.get("model", "Gemini")

        plan_id = f"plan_{len(self._history)}"
        self._history.append({
            "role": "ai",
            "text": message,
            "actions": actions,
            "time": timestamp,
            "plan_id": plan_id,
        })

        self._render_ai_bubble(message, actions, timestamp, is_ai, model, plan_id)

    def _render_ai_bubble(self, message: str, actions: list[dict], timestamp: str, is_ai: bool, model: str, plan_id: str):
        wrap = tk.Frame(self._chat_container, bg=cfg.C("bg"))
        wrap.pack(fill="x", pady=6)

        card = tk.Frame(
            wrap,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=16,
            pady=12,
        )
        card.pack(side="left", fill="x", expand=True)

        # Header info
        top = tk.Frame(card, bg=cfg.C("card"))
        top.pack(fill="x")

        source_label = f"🤖  OneDesk AI ({model})" if is_ai else "🤖  OneDesk AI (Offline NLP)"
        tk.Label(
            top,
            text=source_label,
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("accent") if is_ai else cfg.C("warn"),
        ).pack(side="left")

        tk.Label(
            top,
            text=f" · {timestamp}",
            font=cfg.FONT["xs"],
            bg=cfg.C("card"),
            fg=cfg.C("text3"),
        ).pack(side="left")

        # Conversational text
        tk.Label(
            card,
            text=message,
            font=cfg.FONT["sm"],
            bg=cfg.C("card"),
            fg=cfg.C("text"),
            wraplength=660,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(6, 10))

        # If actions are present, render Action Cards
        if actions:
            actions_box = tk.Frame(card, bg=cfg.C("card2"), padx=12, pady=10)
            actions_box.pack(fill="x", pady=(4, 8))

            tk.Label(
                actions_box,
                text=f"PROPOSED ACTIONS ({len(actions)})",
                font=cfg.FONT["xs_b"],
                bg=cfg.C("card2"),
                fg=cfg.C("text3"),
            ).pack(anchor="w", pady=(0, 6))

            action_row_widgets = []
            for idx, action in enumerate(actions):
                row_w = self._render_action_preview_card(actions_box, action, plan_id, idx)
                action_row_widgets.append((row_w, action))

            # Bottom Action Bar
            bot_bar = tk.Frame(actions_box, bg=cfg.C("card2"))
            bot_bar.pack(fill="x", pady=(8, 0))

            bulk_btn = make_button(
                bot_bar,
                text=f"✓ Confirm & Execute All ({len(actions)})",
                command=lambda p_id=plan_id, acts=actions, btn_ref=bot_bar, rows=action_row_widgets: self._execute_bulk_actions(p_id, acts, btn_ref, rows),
                variant="primary",
                font=cfg.FONT["sm_b"],
                padx=14,
                pady=6,
            )
            bulk_btn.pack(side="left")

            self._pending_plan_cards[plan_id] = {
                "bulk_btn": bulk_btn,
                "rows": action_row_widgets,
            }

        self._scroll_to_bottom()

    def _render_action_preview_card(self, parent, action: dict, plan_id: str, idx: int) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=cfg.C("card"),
            highlightthickness=1,
            highlightbackground=cfg.C("border"),
            padx=12,
            pady=8,
        )
        card.pack(fill="x", pady=3)

        left = tk.Frame(card, bg=cfg.C("card"))
        left.pack(side="left", fill="both", expand=True)

        def _update_card_ui():
            for w in left.winfo_children():
                w.destroy()

            top_line = tk.Frame(left, bg=cfg.C("card"))
            top_line.pack(fill="x")

            kind = action.get("type", "")
            title = action.get("title", "Untitled")

            type_meta = {
                "add_note":  ("📝 NOTE",     cfg.C("accent3")),
                "add_task":  ("✔ TASK",     cfg.C("accent")),
                "add_event": ("📅 CALENDAR", cfg.C("accent2")),
            }.get(kind, ("✦ ACTION", cfg.C("text2")))

            make_pill_badge(
                top_line,
                text=type_meta[0],
                bg=cfg.C("card2"),
                fg=type_meta[1],
                font_key="xs_b",
                padx=6,
                pady=1,
            ).pack(side="left", padx=(0, 8))

            tk.Label(
                top_line,
                text=title,
                font=cfg.FONT["sm_b"],
                bg=cfg.C("card"),
                fg=cfg.C("text"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            meta_items = []
            if kind == "add_task":
                prio = action.get("priority", "Medium")
                meta_items.append(f"Priority: {prio}")
                due = action.get("dueDate")
                if due:
                    meta_items.append(f"Due: {due}")
                cat = action.get("category")
                if cat:
                    meta_items.append(f"Category: {cat}")
            elif kind == "add_event":
                dt = action.get("date")
                tm = action.get("time")
                if dt:
                    meta_items.append(f"Date: {dt}")
                if tm:
                    meta_items.append(f"Time: {tm}")
            elif kind == "add_note":
                desc = action.get("description", "")
                if desc:
                    meta_items.append(desc if len(desc) < 60 else desc[:58] + "…")

            if meta_items:
                tk.Label(
                    left,
                    text="  •  ".join(meta_items),
                    font=cfg.FONT["xs"],
                    bg=cfg.C("card"),
                    fg=cfg.C("text3"),
                    anchor="w",
                ).pack(fill="x", pady=(3, 0))

        _update_card_ui()

        # Right Action Buttons
        right_box = tk.Frame(card, bg=cfg.C("card"))
        right_box.pack(side="right", padx=(8, 0))

        status_lbl = tk.Label(right_box, text="", font=cfg.FONT["xs_b"], bg=cfg.C("card"))
        status_lbl.pack(side="left")

        def _exec_single():
            res = execute_action(self._store, action)
            if res.get("success"):
                exec_btn.pack_forget()
                edit_btn.pack_forget()
                dism_btn.pack_forget()
                status_lbl.configure(text="✓ Applied", fg=cfg.C("success"))
            else:
                status_lbl.configure(text=f"✕ {res.get('message', 'Failed')}", fg=cfg.C("danger"))

        def _dismiss():
            card.destroy()

        exec_btn = make_button(
            right_box,
            text="✓ Execute",
            command=_exec_single,
            variant="secondary",
            font=cfg.FONT["xs_b"],
            padx=8,
            pady=3,
        )
        exec_btn.pack(side="left", padx=2)

        edit_btn = make_button(
            right_box,
            text="✏️ Edit",
            command=lambda: self._open_edit_action_dialog(action, _update_card_ui),
            variant="ghost",
            font=cfg.FONT["xs_b"],
            padx=6,
            pady=3,
        )
        edit_btn.pack(side="left", padx=2)

        dism_btn = make_button(
            right_box,
            text="✕",
            command=_dismiss,
            variant="ghost",
            font=cfg.FONT["xs_b"],
            padx=6,
            pady=3,
        )
        dism_btn.pack(side="left")

        card._exec_single = _exec_single
        card._status_lbl = status_lbl
        card._exec_btn = exec_btn
        card._edit_btn = edit_btn
        card._dism_btn = dism_btn

        return card

    def _open_edit_action_dialog(self, action: dict, on_saved):
        dlg = tk.Toplevel(self)
        kind = action.get("type", "")
        kind_label = {
            "add_note": "Note",
            "add_task": "Task",
            "add_event": "Calendar Event",
        }.get(kind, "Action")

        dlg.title(f"Edit Proposed {kind_label}")
        dlg.configure(bg=cfg.C("bg"))
        dlg.geometry("500x480")
        dlg.minsize(440, 420)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        inner = tk.Frame(dlg, bg=cfg.C("bg"), padx=20, pady=20)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner,
            text=f"✏️  Edit Proposed {kind_label}",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(anchor="w")

        tk.Label(
            inner,
            text="Tweak the action details before confirming and adding to OneDesk.",
            font=cfg.FONT["xs"],
            bg=cfg.C("bg"),
            fg=cfg.C("text2"),
        ).pack(anchor="w", pady=(2, 12))

        # Title Field
        tk.Label(inner, text="Title / Summary:", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
        t_box = tk.Frame(inner, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
        t_box.pack(fill="x", pady=(2, 10))
        title_var = tk.StringVar(value=action.get("title", ""))
        title_entry = tk.Entry(
            t_box,
            textvariable=title_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
        )
        title_entry.pack(fill="x", padx=8, ipady=4)

        desc_text = None
        prio_var = None
        due_var = None
        cat_var = None
        date_var = None
        time_var = None

        if kind == "add_task":
            # Priority
            tk.Label(inner, text="Priority:", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
            prio_var = tk.StringVar(value=action.get("priority", "Medium"))
            p_row = tk.Frame(inner, bg=cfg.C("bg"))
            p_row.pack(anchor="w", pady=(2, 10))
            for p in ["High", "Medium", "Low"]:
                tk.Radiobutton(
                    p_row,
                    text=p,
                    value=p,
                    variable=prio_var,
                    font=cfg.FONT["xs"],
                    bg=cfg.C("bg"),
                    fg=cfg.C("text"),
                    selectcolor=cfg.C("card2"),
                    activebackground=cfg.C("bg"),
                ).pack(side="left", padx=(0, 12))

            # Due Date & Category Row
            dc_row = tk.Frame(inner, bg=cfg.C("bg"))
            dc_row.pack(fill="x", pady=(0, 10))

            # Due Date
            d_left = tk.Frame(dc_row, bg=cfg.C("bg"))
            d_left.pack(side="left", fill="x", expand=True, padx=(0, 6))
            tk.Label(d_left, text="Due Date (YYYY-MM-DD):", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
            due_box = tk.Frame(d_left, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
            due_box.pack(fill="x", pady=(2, 0))
            due_var = tk.StringVar(value=action.get("dueDate", ""))
            tk.Entry(due_box, textvariable=due_var, font=cfg.FONT["sm"], bg=cfg.C("card2"), fg=cfg.C("text"), insertbackground=cfg.C("text"), relief="flat", bd=0).pack(fill="x", padx=8, ipady=4)

            # Category
            c_right = tk.Frame(dc_row, bg=cfg.C("bg"))
            c_right.pack(side="left", fill="x", expand=True, padx=(6, 0))
            tk.Label(c_right, text="Category:", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
            cat_box = tk.Frame(c_right, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
            cat_box.pack(fill="x", pady=(2, 0))
            cat_var = tk.StringVar(value=action.get("category", "General"))
            tk.Entry(cat_box, textvariable=cat_var, font=cfg.FONT["sm"], bg=cfg.C("card2"), fg=cfg.C("text"), insertbackground=cfg.C("text"), relief="flat", bd=0).pack(fill="x", padx=8, ipady=4)

        elif kind == "add_event":
            dt_row = tk.Frame(inner, bg=cfg.C("bg"))
            dt_row.pack(fill="x", pady=(0, 10))

            # Date
            d_left = tk.Frame(dt_row, bg=cfg.C("bg"))
            d_left.pack(side="left", fill="x", expand=True, padx=(0, 6))
            tk.Label(d_left, text="Date (YYYY-MM-DD):", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
            d_box = tk.Frame(d_left, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
            d_box.pack(fill="x", pady=(2, 0))
            date_var = tk.StringVar(value=action.get("date", ""))
            tk.Entry(d_box, textvariable=date_var, font=cfg.FONT["sm"], bg=cfg.C("card2"), fg=cfg.C("text"), insertbackground=cfg.C("text"), relief="flat", bd=0).pack(fill="x", padx=8, ipady=4)

            # Time
            t_right = tk.Frame(dt_row, bg=cfg.C("bg"))
            t_right.pack(side="left", fill="x", expand=True, padx=(6, 0))
            tk.Label(t_right, text="Time (e.g. 09:00 PM):", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
            tm_box = tk.Frame(t_right, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
            tm_box.pack(fill="x", pady=(2, 0))
            time_var = tk.StringVar(value=action.get("time", ""))
            tk.Entry(tm_box, textvariable=time_var, font=cfg.FONT["sm"], bg=cfg.C("card2"), fg=cfg.C("text"), insertbackground=cfg.C("text"), relief="flat", bd=0).pack(fill="x", padx=8, ipady=4)

        # Description / Content (All types or Note)
        tk.Label(inner, text="Description / Content:", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), fg=cfg.C("text2")).pack(anchor="w")
        desc_box = tk.Frame(inner, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
        desc_box.pack(fill="both", expand=True, pady=(2, 12))
        desc_text = tk.Text(
            desc_box,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            height=4,
            wrap="word",
        )
        desc_text.pack(fill="both", expand=True, padx=8, pady=6)
        desc_text.insert("1.0", action.get("description", ""))

        # Buttons
        btn_box = tk.Frame(inner, bg=cfg.C("bg"))
        btn_box.pack(fill="x", side="bottom")

        def _save_changes():
            action["title"] = title_var.get().strip() or "Untitled"
            if desc_text:
                action["description"] = desc_text.get("1.0", "end-1c").strip()
            if kind == "add_task":
                if prio_var:
                    action["priority"] = prio_var.get()
                if due_var:
                    action["dueDate"] = due_var.get().strip()
                if cat_var:
                    action["category"] = cat_var.get().strip() or "General"
            elif kind == "add_event":
                if date_var:
                    action["date"] = date_var.get().strip()
                if time_var:
                    action["time"] = time_var.get().strip()

            on_saved()
            dlg.destroy()

        make_button(btn_box, "✓ Save Changes", command=_save_changes, variant="primary", font=cfg.FONT["sm_b"]).pack(side="left")
        make_button(btn_box, "Cancel", command=dlg.destroy, variant="ghost", font=cfg.FONT["sm_b"]).pack(side="right")

    def _execute_bulk_actions(self, plan_id: str, actions: list[dict], bar_frame: tk.Frame, rows: list):
        count, results = execute_actions(self._store, actions)

        for card_w, _ in rows:
            if card_w.winfo_exists() and hasattr(card_w, "_status_lbl"):
                if hasattr(card_w, "_exec_btn"): card_w._exec_btn.pack_forget()
                if hasattr(card_w, "_edit_btn"): card_w._edit_btn.pack_forget()
                if hasattr(card_w, "_dism_btn"): card_w._dism_btn.pack_forget()
                card_w._status_lbl.configure(text="✓ Applied", fg=cfg.C("success"))

        for w in bar_frame.winfo_children():
            w.destroy()

        tk.Label(
            bar_frame,
            text=f"✓ All {count} actions applied to OneDesk!",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("card2"),
            fg=cfg.C("success"),
        ).pack(side="left", pady=4)

    def _scroll_to_bottom(self):
        self.update_idletasks()
        try:
            self._scroll.canvas.yview_moveto(1.0)
        except Exception:
            pass

    # ── Quick Gemini Configuration Modal ──────────────────────────────────────
    def _open_quick_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Configure Google Gemini AI")
        dlg.configure(bg=cfg.C("bg"))
        dlg.geometry("540x480")
        dlg.minsize(460, 400)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        pad = 20
        inner = tk.Frame(dlg, bg=cfg.C("bg"), padx=pad, pady=pad)
        inner.pack(fill="both", expand=True)

        tk.Label(
            inner,
            text="🤖  Google Gemini Setup",
            font=cfg.FONT["xl_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(anchor="w")

        tk.Label(
            inner,
            text="Connect your free Google Gemini API key to unlock natural-language action planning across your OneDesk notes, tasks, and calendar.",
            font=cfg.FONT["xs"],
            bg=cfg.C("bg"),
            fg=cfg.C("text2"),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(4, 10))

        # Get Free API Key Link Box
        key_help_box = tk.Frame(inner, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"), padx=12, pady=10)
        key_help_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            key_help_box,
            text="Need an API key? Google AI Studio offers free Gemini API access (15 RPM) with no credit card required.",
            font=cfg.FONT["xs"],
            bg=cfg.C("card2"),
            fg=cfg.C("text2"),
            wraplength=460,
            justify="left",
        ).pack(anchor="w")

        make_button(
            key_help_box,
            text="🔗 Get Free Gemini API Key (Google AI Studio)",
            command=lambda: webbrowser.open_new_tab("https://aistudio.google.com/app/apikey"),
            variant="secondary",
            font=cfg.FONT["xs_b"],
            padx=10,
            pady=3,
        ).pack(anchor="w", pady=(6, 0))

        # API Key input
        tk.Label(
            inner,
            text="Gemini API Key:",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(anchor="w")

        key_outer = tk.Frame(inner, bg=cfg.C("card2"), highlightthickness=1, highlightbackground=cfg.C("border"))
        key_outer.pack(fill="x", pady=(4, 8))

        curr_key = get_gemini_api_key()
        key_var = tk.StringVar(value=curr_key)
        key_entry = tk.Entry(
            key_outer,
            textvariable=key_var,
            font=cfg.FONT["sm"],
            bg=cfg.C("card2"),
            fg=cfg.C("text"),
            insertbackground=cfg.C("text"),
            relief="flat",
            bd=0,
            show="•",
        )
        key_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=5)

        show_var = tk.BooleanVar(value=False)
        def _toggle_mask():
            key_entry.configure(show="" if show_var.get() else "•")
            mask_btn.configure(text="Hide" if show_var.get() else "Show")

        def _on_mask_click():
            show_var.set(not show_var.get())
            _toggle_mask()

        mask_btn = tk.Button(
            key_outer,
            text="Show",
            font=cfg.FONT["xs_b"],
            bg=cfg.C("card"),
            fg=cfg.C("text2"),
            relief="flat",
            bd=0,
            padx=8,
            cursor="hand2",
            command=_on_mask_click,
        )
        mask_btn.pack(side="right", padx=4, pady=2)

        # Model Selector
        tk.Label(
            inner,
            text="Gemini Model:",
            font=cfg.FONT["sm_b"],
            bg=cfg.C("bg"),
            fg=cfg.C("text"),
        ).pack(anchor="w", pady=(8, 2))

        curr_model = get_gemini_model()
        model_var = tk.StringVar(value=curr_model)
        m_row = tk.Frame(inner, bg=cfg.C("bg"))
        m_row.pack(anchor="w", pady=(0, 12))

        for m_name in ["gemini-flash-latest", "gemini-3.8-flash", "gemini-3.5-flash"]:
            tk.Radiobutton(
                m_row,
                text=m_name,
                value=m_name,
                variable=model_var,
                font=cfg.FONT["xs_b"],
                bg=cfg.C("bg"),
                fg=cfg.C("text"),
                selectcolor=cfg.C("card2"),
                activebackground=cfg.C("bg"),
            ).pack(side="left", padx=(0, 12))

        status_lbl = tk.Label(inner, text="", font=cfg.FONT["xs_b"], bg=cfg.C("bg"), wraplength=460)
        status_lbl.pack(anchor="w", pady=(2, 10))

        # Buttons
        btn_row = tk.Frame(inner, bg=cfg.C("bg"))
        btn_row.pack(fill="x", pady=(10, 0))

        def _test_conn():
            status_lbl.configure(text="Testing connection to Gemini…", fg=cfg.C("accent"))
            dlg.update_idletasks()
            ok, msg = test_gemini_connection(key_var.get().strip(), model_var.get())
            if ok:
                status_lbl.configure(text=f"✓ {msg}", fg=cfg.C("success"))
            else:
                status_lbl.configure(text=f"✕ {msg}", fg=cfg.C("danger"))

        def _save():
            k = key_var.get().strip()
            m = model_var.get()
            save_data(KEYS.GEMINI_API_KEY, k)
            save_data(KEYS.GEMINI_MODEL, m)
            self._render_header()
            dlg.destroy()

        make_button(
            btn_row,
            text="Test Key",
            command=_test_conn,
            variant="secondary",
            font=cfg.FONT["sm_b"],
        ).pack(side="left", padx=(0, 8))

        make_button(
            btn_row,
            text="Save Settings",
            command=_save,
            variant="primary",
            font=cfg.FONT["sm_b"],
        ).pack(side="left")

        make_button(
            btn_row,
            text="Cancel",
            command=dlg.destroy,
            variant="ghost",
            font=cfg.FONT["sm_b"],
        ).pack(side="right")
