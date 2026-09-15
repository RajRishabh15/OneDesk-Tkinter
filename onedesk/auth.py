"""
OneDesk Auth — auth.py
User session management: demo login, signup, login, profile update.
"""

import uuid
from .storage import load_data, save_data, remove_data, KEYS

# ── Demo user ────────────────────────────────────────────────────────────────

DEMO_USER = {
    "id": "demo-user-alex",
    "name": "Alex Rivera",
    "email": "alex@lifeos.workspace",
}


def _hash(password: str) -> str:
    """Toy hash — keeps passwords out of plain-text storage (demo only)."""
    h = 0
    for ch in password:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    return str(h)


# ── Auth manager ─────────────────────────────────────────────────────────────

class AuthManager:
    def __init__(self):
        self._user: dict | None = load_data(KEYS.USER, None)
        self.error: str = ""

    # ── Properties ──────────────────────────────────────────────────────────
    @property
    def user(self) -> dict | None:
        return self._user

    @property
    def is_logged_in(self) -> bool:
        return self._user is not None

    @property
    def display_name(self) -> str:
        return self._user.get("name", "User") if self._user else "Guest"

    # ── Actions ─────────────────────────────────────────────────────────────
    def demo_login(self) -> bool:
        self.error = ""
        self._user = DEMO_USER
        save_data(KEYS.USER, DEMO_USER)
        return True

    def login(self, email: str, password: str) -> bool:
        self.error = ""
        if email == DEMO_USER["email"]:
            return self.demo_login()
        users = load_data(KEYS.USERS, [])
        match = next(
            (u for u in users if u["email"] == email and u["passwordHash"] == _hash(password)),
            None,
        )
        if not match:
            self.error = "Email or password is incorrect."
            return False
        public = {"id": match["id"], "name": match["name"], "email": match["email"]}
        self._user = public
        save_data(KEYS.USER, public)
        return True

    def signup(self, name: str, email: str, password: str) -> bool:
        self.error = ""
        users = load_data(KEYS.USERS, [])
        if any(u["email"] == email for u in users):
            self.error = "An account with this email already exists."
            return False
        new_user = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "passwordHash": _hash(password),
        }
        save_data(KEYS.USERS, [*users, new_user])
        public = {"id": new_user["id"], "name": name, "email": email}
        self._user = public
        save_data(KEYS.USER, public)
        return True

    def logout(self) -> None:
        self._user = None
        remove_data(KEYS.USER)

    def update_profile(self, name: str = None, email: str = None) -> None:
        if not self._user:
            return
        patch = {}
        if name:
            patch["name"] = name
        if email:
            patch["email"] = email
        self._user = {**self._user, **patch}
        save_data(KEYS.USER, self._user)
        # also update the users list
        users = load_data(KEYS.USERS, [])
        users = [
            {**u, **patch} if u["id"] == self._user["id"] else u
            for u in users
        ]
        save_data(KEYS.USERS, users)
