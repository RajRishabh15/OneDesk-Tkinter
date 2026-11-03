"""Live integration tests; use only randomly generated temporary accounts."""

from contextlib import contextmanager
import hashlib
import unittest
import uuid
from unittest.mock import patch

from argon2 import PasswordHasher

from onedesk import auth as auth_module
from onedesk import db
from onedesk import state as state_module
from onedesk.auth import AuthManager
from onedesk.state import DataStore
from onedesk.storage import KEYS


class MySQLPersistenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        health = db.health_check()
        if not health.ok:
            self.skipTest(f"MySQL is not available: {health.status}")

        self.local_data = {}
        self.account_ids = []

        def local_load(key, fallback=None):
            return self.local_data.get(key, fallback)

        def local_save(key, value):
            self.local_data[key] = value
            return True

        def local_remove(key):
            self.local_data.pop(key, None)

        self.patches = [
            patch.object(auth_module, "load_data", side_effect=local_load),
            patch.object(auth_module, "save_data", side_effect=local_save),
            patch.object(auth_module, "remove_data", side_effect=local_remove),
            patch.object(state_module, "load_data", side_effect=local_load),
            patch.object(state_module, "save_data", side_effect=local_save),
            patch.object(state_module, "remove_data", side_effect=local_remove),
            patch.object(state_module, "export_backup", return_value={"theme": "dark"}),
            patch("onedesk.storage.import_backup", side_effect=lambda values: self.local_data.update(values)),
        ]
        for mocked in self.patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    def _create_account(self, suffix: str) -> AuthManager:
        auth = AuthManager()
        email = f"onedesk-it-{uuid.uuid4().hex}-{suffix}@example.test"
        self.assertTrue(auth.signup(f"Integration {suffix}", email, "Test-Password-913!"), auth.error)
        self.account_ids.append(auth.user["id"])
        return auth

    def tearDown(self):
        if not self.account_ids:
            return
        with db.transaction() as conn:
            cur = conn.cursor()
            try:
                for user_id in self.account_ids:
                    cur.execute("DELETE FROM notes WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM tasks WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM events WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM tags WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM categories WHERE user_id=%s", (user_id,))
                    cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            finally:
                cur.close()

    def test_full_account_persistence_migration_and_backup(self):
        auth1 = self._create_account("one")
        original_id = auth1.user["id"]
        user_row = db.query(
            "SELECT id,password_hash FROM users WHERE id=%(id)s", {"id": original_id}
        )[0]
        account_email = auth1.user["email"]
        self.assertTrue(user_row["password_hash"].startswith("$argon2id$"))
        self.assertTrue(PasswordHasher().verify(user_row["password_hash"], "Test-Password-913!"))
        auth1._user = None
        self.assertFalse(auth1.login(account_email, "incorrect-password"))
        self.assertTrue(auth1.login(account_email, "Test-Password-913!"), auth1.error)
        self.assertTrue(auth1.update_profile(name="Updated Integration User"), auth1.error)
        self.assertEqual(db.query("SELECT name FROM users WHERE id=%(id)s", {"id": original_id})[0]["name"],
                         "Updated Integration User")

        duplicate = AuthManager()
        self.assertFalse(duplicate.signup("Duplicate", auth1.user["email"], "Another-Password-913!"))
        self.assertIn("already exists", duplicate.error)

        store1 = DataStore()
        store1.set_user(auth1.user["id"])
        note = store1.add_note(title="Integration note", description="before", category="Study",
                               tags=["database", "one"], color="cyan")
        store1.update_note(note["id"], title="Updated note", tags=["database", "two"])
        store1.toggle_pin(note["id"])
        self.assertEqual(store1.notes[0]["title"], "Updated note")
        self.assertTrue(store1.notes[0]["pinned"])
        self.assertEqual(set(store1.notes[0]["tags"]), {"database", "two"})

        task = store1.add_task(title="Integration task", description="task body", category="Study",
                               priority="High", dueDate="2026-12-10")
        store1.set_task_status(task["id"], "Completed")
        self.assertEqual(store1.tasks[0]["status"], "Completed")
        self.assertIsNotNone(store1.tasks[0]["completedAt"])

        event = store1.add_event(title="Integration event", date="2026-12-11", time="09:30 AM",
                                 reminder=True, description="event body")
        store1.update_event(event["id"], time="10:45 AM", reminder=False)
        self.assertEqual(store1.events[0]["time"], "10:45 AM")
        self.assertFalse(store1.events[0]["reminder"])

        auth2 = self._create_account("two")
        store2 = DataStore()
        store2.set_user(auth2.user["id"])
        store2.add_note(title="Private second account", category="Private", tags=["private"])
        self.assertEqual(len(store1.notes), 1)
        self.assertNotIn("Private second account", [item["title"] for item in store1.notes])

        backup = store1.get_backup()
        self.assertEqual(len(backup["notes"]), 1)
        self.assertEqual(len(backup["tasks"]), 1)
        self.assertEqual(len(backup["events"]), 1)
        self.assertNotIn("user", backup)

        store1.clear_all()
        self.assertEqual((store1.notes, store1.tasks, store1.events), ([], [], []))
        self.assertEqual(db.query("SELECT id FROM users WHERE id=%(id)s", {"id": auth1.user["id"]})[0]["id"], auth1.user["id"])
        self.assertEqual(len(store2.notes), 1)
        store1.restore_backup(backup)
        self.assertEqual((len(store1.notes), len(store1.tasks), len(store1.events)), (1, 1, 1))
        self.assertEqual(store1.notes[0]["tags"], ["database", "two"])

        store1.delete_note(note["id"])
        store1.delete_task(task["id"])
        store1.delete_event(event["id"])
        self.assertEqual((store1.notes, store1.tasks, store1.events), ([], [], []))
        self.assertEqual(db.query("SELECT COUNT(*) AS n FROM notes WHERE user_id=%(id)s", {"id": auth1.user["id"]})[0]["n"], 0)
        self.assertEqual(db.query("SELECT COUNT(*) AS n FROM note_tags WHERE user_id=%(id)s", {"id": auth1.user["id"]})[0]["n"], 0)

        # The old local store has no owner column. Migration is enabled only
        # when the recorded local profile email matches the MySQL account.
        self.local_data[KEYS.LEGACY_DATA_OWNER] = "another-person@example.test"
        self.local_data[KEYS.NOTES] = [{"id": "unassigned", "title": "Unmatched legacy note"}]
        unmatched = DataStore()
        unmatched.set_user(auth1.user["id"], migrate_legacy=False)
        self.assertEqual(unmatched.notes, [])
        self.assertIn(KEYS.NOTES, self.local_data)

        self.local_data[KEYS.LEGACY_DATA_OWNER] = auth1.user["email"].casefold()
        self.local_data[KEYS.USER] = dict(auth1.user)
        self.local_data[KEYS.NOTES] = [
            {"id": store2.notes[0]["id"], "title": "Legacy collision note", "category": "Old",
             "tags": ["legacy"], "color": "not-supported", "createdAt": "2024-02-03"},
            {"id": "bad-id", "title": "Legacy generated ID", "category": "Old",
             "tags": ["generated"], "color": "green", "createdAt": "2024-02-03"},
        ]
        self.local_data[KEYS.TASKS] = [{"id": str(uuid.uuid4()), "title": "Legacy task", "status": "unknown",
                                        "priority": "Urgent", "dueDate": "2024-02-04", "category": "Old"}]
        self.local_data[KEYS.EVENTS] = [
            {"id": str(uuid.uuid4()), "title": "Legacy event", "date": "2024-02-05",
             "time": "14:15", "reminder": True},
            {"id": "bad-event-id", "title": "Legacy event with bad time", "date": "2024-02-06",
             "time": "not-a-time", "reminder": "false"},
        ]
        resumed_auth = AuthManager()
        self.assertTrue(resumed_auth.can_migrate_legacy_data)
        migrated = DataStore()
        migrated.set_user(resumed_auth.user["id"], migrate_legacy=True)
        self.assertEqual({item["title"] for item in migrated.notes},
                         {"Legacy collision note", "Legacy generated ID"})
        legacy_collision_note = next(item for item in migrated.notes if item["title"] == "Legacy collision note")
        self.assertNotEqual(legacy_collision_note["id"], store2.notes[0]["id"])
        self.assertEqual(legacy_collision_note["color"], "violet")
        self.assertEqual(legacy_collision_note["tags"], ["legacy"])
        self.assertEqual(migrated.tasks[0]["priority"], "Medium")
        self.assertEqual(migrated.tasks[0]["status"], "Todo")
        self.assertEqual(next(item for item in migrated.events if item["title"] == "Legacy event")["time"], "02:15 PM")
        invalid_event = next(item for item in migrated.events if item["title"] == "Legacy event with bad time")
        self.assertEqual(invalid_event["time"], "10:00 AM")
        self.assertFalse(invalid_event["reminder"])
        self.assertNotIn(KEYS.NOTES, self.local_data)

        migrated.set_user(resumed_auth.user["id"], migrate_legacy=True)
        self.assertEqual((len(migrated.notes), len(migrated.tasks), len(migrated.events)), (2, 1, 2))
        self.assertEqual(db.query("SELECT COUNT(*) AS n FROM notes WHERE user_id=%(id)s", {"id": auth1.user["id"]})[0]["n"], 2)
        self.assertEqual(db.query("SELECT COUNT(*) AS n FROM notes WHERE user_id=%(id)s", {"id": auth2.user["id"]})[0]["n"], 1)

    def test_legacy_sha256_login_rehashes_to_argon2id(self):
        auth = AuthManager()
        clear_text = "Legacy-Password-913!"
        old_hash = hashlib.sha256(clear_text.encode("utf-8")).hexdigest()
        row = {"id": str(uuid.uuid4()), "name": "Legacy", "email": "legacy@example.test",
               "password_hash": old_hash, "avatar_path": ""}
        captured = {}

        class Cursor:
            rowcount = 1
            def execute(self, sql, params=None):
                captured["sql"] = sql
                captured["params"] = params
            def close(self):
                pass

        class Connection:
            def cursor(self):
                return Cursor()
            def commit(self):
                pass
            def rollback(self):
                pass

        @contextmanager
        def fake_transaction():
            yield Connection()

        with patch.object(auth_module.db, "query", return_value=[row]), \
             patch.object(auth_module.db, "transaction", fake_transaction):
            self.assertTrue(auth.login(row["email"], clear_text), auth.error)
        upgraded_hash = captured["params"]["password_hash"]
        self.assertTrue(upgraded_hash.startswith("$argon2id$"))
        self.assertTrue(PasswordHasher().verify(upgraded_hash, clear_text))
        self.assertIn("UPDATE users SET password_hash", captured["sql"])

    def test_authentication_does_not_fall_back_to_json(self):
        self.local_data[KEYS.USERS] = [{
            "id": str(uuid.uuid4()),
            "name": "JSON-only account",
            "email": "json-only@example.test",
            "passwordHash": hashlib.sha256(b"legacy-password").hexdigest(),
        }]
        manager = AuthManager()

        class UnavailableDatabaseError(Exception):
            errno = 2003

        with patch.object(auth_module.db, "query", side_effect=UnavailableDatabaseError()):
            self.assertFalse(manager.login("json-only@example.test", "legacy-password"))
        self.assertFalse(manager.is_logged_in)
        self.assertIn("could not reach MySQL", manager.error)

    def test_demo_login_ensures_a_valid_uuid_user_with_argon_hash(self):
        manager = AuthManager()
        inserted = {}
        demo_id = auth_module.DEMO_USER["id"]
        row = {**auth_module.DEMO_USER}

        class Cursor:
            def execute(self, sql, params=None):
                inserted.update(params or {})
            def close(self):
                pass

        class Connection:
            def cursor(self):
                return Cursor()

        @contextmanager
        def fake_transaction():
            yield Connection()

        with patch.object(auth_module.db, "query", side_effect=[[], [row]]), \
             patch.object(auth_module.db, "transaction", fake_transaction):
            self.assertTrue(manager.demo_login(), manager.error)

        self.assertEqual(manager.user["id"], demo_id)
        self.assertEqual(str(uuid.UUID(manager.user["id"])), manager.user["id"])
        self.assertTrue(inserted["password_hash"].startswith("$argon2id$"))


if __name__ == "__main__":
    unittest.main()
