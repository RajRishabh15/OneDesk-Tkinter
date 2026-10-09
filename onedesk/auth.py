"""
OneDesk Auth - auth.py
User session management.
Uses MySQL when available, falls back to JSON storage automatically.
"""

import uuid
import hashlib
from .storage import load_data, save_data, remove_data, KEYS

try:
    from . import db as _db
    _USE_DB = _db.is_available()
except Exception:
    _USE_DB = False

DEMO_USER = {
    "id":    "demo-user-alex",
    "name":  "Alex Rivera",
    "email": "alex@lifeos.workspace",
}


def _hash(password: str) -> str:
    """SHA-256 hash."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthManager:
    def __init__(self):
        self._user = load_data(KEYS.USER, None)
        self.error = ""

    @property
    def user(self):         return self._user
    @property
    def is_logged_in(self): return self._user is not None
    @property
    def display_name(self):
        return self._user.get("name", "User") if self._user else "Guest"

    def demo_login(self) -> bool:
        self.error = ""
        self._user = DEMO_USER
        save_data(KEYS.USER, DEMO_USER)
        return True

    def login(self, email: str, password: str) -> bool:
        self.error = ""
        if email == DEMO_USER["email"]:
            return self.demo_login()
        return self._login_db(email, password) if _USE_DB else self._login_json(email, password)

    def signup(self, name: str, email: str, password: str) -> bool:
        self.error = ""
        return self._signup_db(name, email, password) if _USE_DB else self._signup_json(name, email, password)

    def logout(self) -> None:
        self._user = None
        remove_data(KEYS.USER)

    def update_profile(self, name: str = None, email: str = None) -> None:
        if not self._user: return
        patch = {}
        if name:  patch["name"]  = name
        if email: patch["email"] = email
        self._user = {**self._user, **patch}
        save_data(KEYS.USER, self._user)
        if _USE_DB:
            _db.execute(
                "UPDATE users SET name=%(n)s, email=%(e)s WHERE id=%(i)s",
                {"n": self._user["name"], "e": self._user["email"], "i": self._user["id"]}
            )
        else:
            users = load_data(KEYS.USERS, [])
            save_data(KEYS.USERS, [{**u, **patch} if u["id"] == self._user["id"] else u for u in users])

    # ── DB helpers ──────────────────────────────────────────────────────
    def _login_db(self, email, password):
        rows = _db.query("SELECT id,name,email,password_hash FROM users WHERE email=%(e)s", {"e": email})
        if not rows or rows[0]["password_hash"] != _hash(password):
            self.error = "Email or password is incorrect."
            return False
        u = rows[0]
        public = {"id": u["id"], "name": u["name"], "email": u["email"]}
        self._user = public
        save_data(KEYS.USER, public)
        return True

    def _signup_db(self, name, email, password):
        if _db.query("SELECT id FROM users WHERE email=%(e)s", {"e": email}):
            self.error = "An account with this email already exists."
            return False
        uid = str(uuid.uuid4())
        _db.execute(
            "INSERT INTO users (id,name,email,password_hash) VALUES (%(i)s,%(n)s,%(e)s,%(p)s)",
            {"i": uid, "n": name, "e": email, "p": _hash(password)}
        )
        public = {"id": uid, "name": name, "email": email}
        self._user = public
        save_data(KEYS.USER, public)
        return True

    # ── JSON fallback ────────────────────────────────────────────────────
    def _login_json(self, email, password):
        users = load_data(KEYS.USERS, [])
        match = next((u for u in users if u["email"] == email and u["passwordHash"] == _hash(password)), None)
        if not match:
            self.error = "Email or password is incorrect."
            return False
        public = {"id": match["id"], "name": match["name"], "email": match["email"]}
        self._user = public
        save_data(KEYS.USER, public)
        return True

    def _signup_json(self, name, email, password):
        users = load_data(KEYS.USERS, [])
        if any(u["email"] == email for u in users):
            self.error = "An account with this email already exists."
            return False
        new_user = {"id": str(uuid.uuid4()), "name": name, "email": email, "passwordHash": _hash(password)}
        save_data(KEYS.USERS, [*users, new_user])
        public = {"id": new_user["id"], "name": name, "email": email}
        self._user = public
        save_data(KEYS.USER, public)
        return True
