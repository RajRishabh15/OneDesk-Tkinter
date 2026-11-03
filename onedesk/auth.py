"""MySQL-backed user authentication and profile management."""

from __future__ import annotations

import hashlib
import hmac
import re
import uuid

from argon2 import PasswordHasher, exceptions as argon2_exceptions

from . import db
from .storage import KEYS, load_data, remove_data, save_data


DEMO_USER = {
    "id": "7cf2f5a8-a36d-4d53-9ce8-ea56ac875b1a",
    "name": "Alex Rivera",
    "email": "alex@lifeos.workspace",
    "avatar_path": "",
}

_PASSWORDS = PasswordHasher()
_LEGACY_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _friendly_database_error(exc: Exception) -> str:
    if isinstance(exc, (db.DatabaseConfigurationError, db.DatabaseDriverError)):
        return str(exc)
    errno = getattr(exc, "errno", None)
    if errno in (1044, 1045):
        return "MySQL rejected the configured account. Check DB_USER, DB_PASSWORD, and its permissions."
    if errno == 1049:
        return "The OneDesk database was not found. Create it using setup_db.sql."
    if errno in (2002, 2003, 2005, 2006, 2013):
        return "OneDesk could not reach MySQL. Check that the server is running and DB_HOST/DB_PORT are correct."
    if errno == 1062:
        return "An account with this email already exists."
    return "The database request failed. Check the database connection and try again."


def _public_user(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "email": row["email"],
        "avatar_path": row.get("avatar_path") or "",
    }


def _select_user(sql: str, params: dict) -> dict | None:
    rows = db.query(sql, params)
    return rows[0] if rows else None


class AuthManager:
    def __init__(self):
        self._legacy_user = load_data(KEYS.USER, None)
        prior_session_email = (
            str(self._legacy_user.get("email", "")).strip().casefold()
            if isinstance(self._legacy_user, dict)
            else ""
        )
        owner_email = load_data(KEYS.LEGACY_DATA_OWNER, "__unset__")
        if owner_email == "__unset__":
            owner_email = prior_session_email
            save_data(KEYS.LEGACY_DATA_OWNER, owner_email)
        self._legacy_identity_email = str(owner_email or "").strip().casefold()
        self._migration_allowed = False
        self._user = None
        self.error = ""

        # A local session is restored only after confirming its account exists
        # in MySQL. Local JSON is never used to authenticate an account.
        if isinstance(self._legacy_user, dict):
            email = str(self._legacy_user.get("email", "")).strip()
            if email.casefold() == DEMO_USER["email"].casefold():
                self.demo_login()
            elif self._legacy_user.get("id"):
                try:
                    row = _select_user(
                        "SELECT id, name, email, avatar_path FROM users WHERE id=%(id)s",
                        {"id": str(self._legacy_user["id"])},
                    )
                    if row:
                        self._user = _public_user(row)
                        save_data(KEYS.USER, self._user)
                        self._migration_allowed = (
                            self._legacy_identity_email == str(row["email"]).strip().casefold()
                        )
                    else:
                        remove_data(KEYS.USER)
                        self.error = "The saved account no longer exists in MySQL. Please sign in."
                except Exception as exc:
                    self.error = _friendly_database_error(exc)

    @property
    def user(self):
        return self._user

    @property
    def is_logged_in(self):
        return self._user is not None

    @property
    def display_name(self):
        return self._user.get("name", "User") if self._user else "Guest"

    @property
    def avatar_path(self):
        return self._user.get("avatar_path", "") if self._user else ""

    @property
    def can_migrate_legacy_data(self) -> bool:
        """Whether the previous local profile matches this authenticated user."""
        return bool(self._migration_allowed and self._user)

    def _set_authenticated_user(self, row: dict, email: str) -> None:
        self._user = _public_user(row)
        save_data(KEYS.USER, self._user)
        self._migration_allowed = bool(
            self._legacy_identity_email
            and self._legacy_identity_email == email.strip().casefold()
        )

    def demo_login(self) -> bool:
        self.error = ""
        try:
            row = _select_user(
                "SELECT id, name, email, avatar_path FROM users WHERE email=%(email)s",
                {"email": DEMO_USER["email"]},
            )
            if row is None:
                # Demo has no user-entered password. Store a random, unusable
                # secret using the same Argon2id format required by the schema.
                demo_hash = _PASSWORDS.hash(uuid.uuid4().hex)
                try:
                    with db.transaction() as conn:
                        cur = conn.cursor()
                        try:
                            cur.execute(
                                "INSERT INTO users (id,name,email,password_hash,avatar_path) "
                                "VALUES (%(id)s,%(name)s,%(email)s,%(password_hash)s,%(avatar_path)s)",
                                {
                                    "id": DEMO_USER["id"],
                                    "name": DEMO_USER["name"],
                                    "email": DEMO_USER["email"],
                                    "password_hash": demo_hash,
                                    "avatar_path": "",
                                },
                            )
                        finally:
                            cur.close()
                except Exception:
                    # Handle concurrent demo startup by re-reading the unique
                    # email; other database errors remain visible below.
                    row = _select_user(
                        "SELECT id, name, email, avatar_path FROM users WHERE email=%(email)s",
                        {"email": DEMO_USER["email"]},
                    )
                    if row is None:
                        raise
                if row is None:
                    row = _select_user(
                        "SELECT id, name, email, avatar_path FROM users WHERE email=%(email)s",
                        {"email": DEMO_USER["email"]},
                    )
            if row is None:
                raise RuntimeError("Demo account could not be created.")
            self._set_authenticated_user(row, DEMO_USER["email"])
            return True
        except Exception as exc:
            self.error = _friendly_database_error(exc)
            return False

    def login(self, email: str, password: str) -> bool:
        self.error = ""
        email = email.strip()
        if email.casefold() == DEMO_USER["email"].casefold():
            return self.demo_login()
        try:
            row = _select_user(
                "SELECT id, name, email, password_hash, avatar_path FROM users WHERE email=%(email)s",
                {"email": email},
            )
            if row is None or not self._verify_password(row["password_hash"], password):
                self.error = "Email or password is incorrect."
                return False

            stored_hash = row["password_hash"]
            if _LEGACY_SHA256_RE.fullmatch(stored_hash):
                upgraded_hash = _PASSWORDS.hash(password)
                with db.transaction() as conn:
                    cur = conn.cursor()
                    try:
                        cur.execute(
                            "UPDATE users SET password_hash=%(password_hash)s WHERE id=%(id)s AND password_hash=%(old_hash)s",
                            {"password_hash": upgraded_hash, "id": row["id"], "old_hash": stored_hash},
                        )
                    finally:
                        cur.close()

            self._set_authenticated_user(row, email)
            return True
        except Exception as exc:
            self.error = _friendly_database_error(exc)
            return False

    @staticmethod
    def _verify_password(stored_hash: str, password: str) -> bool:
        if _LEGACY_SHA256_RE.fullmatch(stored_hash):
            digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return hmac.compare_digest(stored_hash.lower(), digest)
        try:
            return _PASSWORDS.verify(stored_hash, password)
        except (argon2_exceptions.VerifyMismatchError, argon2_exceptions.InvalidHashError):
            return False
        except argon2_exceptions.VerificationError:
            return False

    def signup(self, name: str, email: str, password: str) -> bool:
        self.error = ""
        name = name.strip()
        email = email.strip()
        if not name or not email or not password:
            self.error = "Name, email, and password are required."
            return False
        if email.casefold() == DEMO_USER["email"].casefold():
            self.error = "This email is reserved for the demo account."
            return False
        try:
            user_id = str(uuid.uuid4())
            password_hash = _PASSWORDS.hash(password)
            with db.transaction() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(
                        "INSERT INTO users (id,name,email,password_hash) "
                        "VALUES (%(id)s,%(name)s,%(email)s,%(password_hash)s)",
                        {"id": user_id, "name": name, "email": email, "password_hash": password_hash},
                    )
                finally:
                    cur.close()
            self._set_authenticated_user(
                {"id": user_id, "name": name, "email": email, "avatar_path": ""},
                email,
            )
            return True
        except Exception as exc:
            self.error = _friendly_database_error(exc)
            return False

    def logout(self, *, preserve_session: bool = False) -> None:
        self._user = None
        self._migration_allowed = False
        if not preserve_session:
            remove_data(KEYS.USER)

    def update_profile(self, name: str = None, email: str = None, avatar_path: str = None) -> bool:
        if not self._user:
            self.error = "No authenticated account is active."
            return False
        updated = dict(self._user)
        if name is not None:
            updated["name"] = name.strip()
        if email is not None:
            updated["email"] = email.strip()
        if avatar_path is not None:
            updated["avatar_path"] = avatar_path
        try:
            with db.transaction() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(
                        "UPDATE users SET name=%(name)s,email=%(email)s,avatar_path=%(avatar_path)s WHERE id=%(id)s",
                        {**updated, "id": self._user["id"]},
                    )
                    if cur.rowcount == 0:
                        cur.execute("SELECT 1 FROM users WHERE id=%s", (self._user["id"],))
                        if cur.fetchone() is None:
                            raise RuntimeError("Account was not found.")
                finally:
                    cur.close()
            self._user = updated
            save_data(KEYS.USER, self._user)
            self.error = ""
            return True
        except Exception as exc:
            self.error = _friendly_database_error(exc)
            return False
