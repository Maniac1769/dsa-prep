"""Accounts, sessions and throttling, called directly (no HTTP stack needed)."""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from app import auth, db
from app.errors import Conflict, Forbidden, Invalid, TooMany, Unauthorized

SEED = Path(__file__).resolve().parent.parent / "seed"
NOW = datetime(2026, 10, 12, 9, 0, tzinfo=timezone.utc)
PASSWORD = "correct horse battery"


class AuthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "prep.db"
        db.SEED_DIR = SEED
        self.conn = db.connect()
        db.init(self.conn)
        auth.reset_throttle()
        self.env = mock.patch.dict(os.environ, {"MAX_USERS": "20"})
        self.env.start()
        self.quiet = mock.patch("builtins.print")
        self.quiet.start()

    def tearDown(self) -> None:
        self.quiet.stop()
        self.env.stop()
        self.conn.close()
        self.tmp.cleanup()

    def register(self, name: str = "asha", now: datetime = NOW, **kw):
        return auth.register(self.conn, name, kw.pop("password", PASSWORD), kw.pop("tz", "Asia/Kolkata"), now=now, **kw)

    def count(self, sql: str, *params) -> int:
        return self.conn.execute(sql, params).fetchone()[0]

    # --- register, login, logout ------------------------------------------------------

    def test_register_signs_in_and_stores_only_a_hash_of_the_token(self) -> None:
        user, token = self.register()
        self.assertEqual(user["username"], "asha")
        self.assertEqual(user["preferred_list"], "plan")
        row = self.conn.execute("SELECT token_hash FROM auth_sessions").fetchone()
        self.assertEqual(row["token_hash"], hashlib.sha256(token.encode()).hexdigest())
        self.assertNotIn(token, row["token_hash"])
        resolved, _ = auth.resolve_session(self.conn, token, NOW)
        self.assertEqual(resolved["id"], user["id"])

    def test_password_hash_format_is_scrypt_with_the_contract_parameters(self) -> None:
        user, _ = self.register()
        kind, n, r, p, salt, digest = user["password_hash"].split("$")
        self.assertEqual((kind, n, r, p), ("scrypt", str(2**14), "8", "1"))
        self.assertTrue(salt and digest)
        self.assertNotIn(PASSWORD, user["password_hash"])
        self.assertNotEqual(auth.hash_password(PASSWORD), auth.hash_password(PASSWORD), "salted")

    def test_login_logout_roundtrip(self) -> None:
        self.register()
        user, token = auth.login(self.conn, "ASHA", PASSWORD, now=NOW)  # usernames are case-insensitive
        self.assertIsNotNone(auth.resolve_session(self.conn, token, NOW))
        auth.end_session(self.conn, token)
        self.assertIsNone(auth.resolve_session(self.conn, token, NOW))

    def test_wrong_password_and_unknown_user_look_the_same(self) -> None:
        self.register()
        for name, password in (("asha", "not the password"), ("nobody", PASSWORD)):
            with self.assertRaises(Unauthorized) as ctx:
                auth.login(self.conn, name, password, now=NOW)
            self.assertEqual(str(ctx.exception), "Wrong username or password.")

    def test_unknown_user_still_runs_a_scrypt(self) -> None:
        with mock.patch.object(auth, "verify_password", wraps=auth.verify_password) as verify:
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "ghost", PASSWORD, now=NOW)
        self.assertEqual(verify.call_count, 1)

    def test_username_and_password_rules(self) -> None:
        for bad in ("ab", "x" * 25, "has space", "dot.name", "émile"):
            with self.assertRaises(Invalid, msg=bad):
                self.register(bad)
        for bad in ("short", "x" * 9, "p" * 129):
            with self.assertRaises(Invalid, msg=bad):
                self.register("fine", password=bad)
        self.register("ok_name-1", password="p" * 128)
        with self.assertRaises(Invalid):
            self.register("tzbad", tz="Mars/Olympus")
        with self.assertRaises(Invalid):
            self.register("listbad", preferred_list="nope")

    def test_username_is_unique_ignoring_case(self) -> None:
        self.register("Asha")
        with self.assertRaises(Conflict):
            self.register("aSHA")

    # --- registration cap -------------------------------------------------------------

    def test_registration_cap_is_enforced(self) -> None:
        with mock.patch.dict(os.environ, {"MAX_USERS": "2"}):
            self.register("one")
            self.register("two")
            with self.assertRaises(Forbidden) as ctx:
                self.register("three")
            self.assertEqual(str(ctx.exception), "Sign-ups are full: 2 of 2 places taken.")
            self.assertEqual(self.count("SELECT COUNT(*) FROM users"), 2)
            status = auth.status(self.conn)
            self.assertEqual((status["registration_open"], status["users"], status["cap"]), (False, 2, 2))
            self.assertEqual([entry["key"] for entry in status["lists"]], ["plan", "sde", "a2z"])

    def test_cap_check_and_insert_share_one_write_lock(self) -> None:
        """A second connection cannot slip in between the count and the insert."""
        other = db.connect()
        try:
            with mock.patch.dict(os.environ, {"MAX_USERS": "1"}):
                real_write_txn = db.write_txn
                entered: list[bool] = []

                def spy(conn):
                    cm = real_write_txn(conn)

                    class Wrapped:
                        def __enter__(self_inner):
                            cm.__enter__()
                            entered.append(conn.in_transaction)
                            # While we hold the lock, a competing writer must be refused.
                            other.execute("PRAGMA busy_timeout = 0")
                            with self_outer.assertRaises(Exception) as err:
                                other.execute("BEGIN IMMEDIATE")
                            self_outer.assertIn("locked", str(err.exception))

                        def __exit__(self_inner, *exc):
                            return cm.__exit__(*exc)

                    return Wrapped()

                self_outer = self
                with mock.patch.object(db, "write_txn", spy):
                    self.register("solo")
                self.assertEqual(entered, [True])
        finally:
            other.close()

    # --- throttling --------------------------------------------------------------------

    def test_five_failures_lock_the_username_for_fifteen_minutes(self) -> None:
        self.register()
        for i in range(5):
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "asha", "wrong password!", now=NOW + timedelta(seconds=i))
        with self.assertRaises(TooMany) as ctx:
            auth.login(self.conn, "asha", PASSWORD, now=NOW + timedelta(minutes=10))
        self.assertAlmostEqual(ctx.exception.retry_after, 5 * 60 + 4, delta=2)
        # The right password does not get in while locked, and the lock lifts on time.
        auth.login(self.conn, "asha", PASSWORD, now=NOW + timedelta(minutes=15, seconds=5))

    def test_lockout_is_per_username(self) -> None:
        self.register("asha")
        self.register("ravi")
        for i in range(5):
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "asha", "wrong password!", now=NOW + timedelta(seconds=i))
        auth.login(self.conn, "ravi", PASSWORD, now=NOW + timedelta(seconds=10))

    def test_unknown_names_are_throttled_too(self) -> None:
        for i in range(5):
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "ghost", PASSWORD, now=NOW + timedelta(seconds=i))
        with self.assertRaises(TooMany):
            auth.login(self.conn, "ghost", PASSWORD, now=NOW + timedelta(seconds=6))

    def test_failures_older_than_the_window_do_not_count(self) -> None:
        self.register()
        for i in range(4):
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "asha", "wrong password!", now=NOW + timedelta(minutes=i))
        with self.assertRaises(Unauthorized):  # the first four have aged out by now
            auth.login(self.conn, "asha", "wrong password!", now=NOW + timedelta(minutes=30))
        auth.login(self.conn, "asha", PASSWORD, now=NOW + timedelta(minutes=30, seconds=1))

    def test_success_clears_earlier_failures(self) -> None:
        self.register()
        for i in range(4):
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "asha", "wrong password!", now=NOW + timedelta(seconds=i))
        auth.login(self.conn, "asha", PASSWORD, now=NOW + timedelta(seconds=5))
        with self.assertRaises(Unauthorized):
            auth.login(self.conn, "asha", "wrong password!", now=NOW + timedelta(seconds=6))

    def test_global_limit_is_thirty_attempts_a_minute(self) -> None:
        for i in range(30):
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, f"user{i}", PASSWORD, now=NOW + timedelta(seconds=i))
        with self.assertRaises(TooMany) as ctx:
            auth.login(self.conn, "user31", PASSWORD, now=NOW + timedelta(seconds=31))
        self.assertGreaterEqual(ctx.exception.retry_after, 1)
        with self.assertRaises(TooMany):
            self.register("late", now=NOW + timedelta(seconds=32))
        with self.assertRaises(Unauthorized):  # the minute has rolled over
            auth.login(self.conn, "user99", PASSWORD, now=NOW + timedelta(seconds=75))

    # --- sessions ----------------------------------------------------------------------

    def test_sessions_last_thirty_days_and_refresh_under_fifteen(self) -> None:
        _, token = self.register()
        _, refreshed = auth.resolve_session(self.conn, token, NOW + timedelta(days=10))
        self.assertFalse(refreshed)
        _, refreshed = auth.resolve_session(self.conn, token, NOW + timedelta(days=16))
        self.assertTrue(refreshed)
        # Pushed out to 30 days from the refresh, so it outlives the original expiry.
        self.assertIsNotNone(auth.resolve_session(self.conn, token, NOW + timedelta(days=40)))
        self.assertIsNone(auth.resolve_session(self.conn, token, NOW + timedelta(days=71)))
        self.assertEqual(self.count("SELECT COUNT(*) FROM auth_sessions"), 0, "expired rows are removed")

    def test_garbage_tokens_resolve_to_nothing(self) -> None:
        for token in ("", "nope", "x" * 1000):
            self.assertIsNone(auth.resolve_session(self.conn, token, NOW))

    def test_cookie_secure_defaults_on(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COOKIE_SECURE", None)
            self.assertTrue(auth.cookie_secure())
        with mock.patch.dict(os.environ, {"COOKIE_SECURE": "0"}):
            self.assertFalse(auth.cookie_secure())

    # --- password change, delete, admin ----------------------------------------------------

    def test_password_change_ends_the_other_sessions_only(self) -> None:
        user, here = self.register()
        _, elsewhere = auth.login(self.conn, "asha", PASSWORD, now=NOW)
        other_user, other_token = self.register("ravi")

        auth.change_password(self.conn, user, PASSWORD, "a brand new passphrase", here, now=NOW)

        self.assertIsNotNone(auth.resolve_session(self.conn, here, NOW))
        self.assertIsNone(auth.resolve_session(self.conn, elsewhere, NOW))
        self.assertIsNotNone(auth.resolve_session(self.conn, other_token, NOW))
        with self.assertRaises(Unauthorized):
            auth.login(self.conn, "asha", PASSWORD, now=NOW)
        auth.login(self.conn, "asha", "a brand new passphrase", now=NOW)

    def test_password_change_needs_the_current_password_and_a_valid_new_one(self) -> None:
        user, token = self.register()
        with self.assertRaises(Forbidden):
            auth.change_password(self.conn, user, "wrong wrong wrong", "a brand new passphrase", token, now=NOW)
        with self.assertRaises(Invalid):
            auth.change_password(self.conn, user, PASSWORD, "short", token, now=NOW)
        auth.login(self.conn, "asha", PASSWORD, now=NOW)

    def test_wrong_current_password_counts_toward_the_lockout(self) -> None:
        user, token = self.register()
        for _ in range(5):
            with self.assertRaises(Forbidden):
                auth.confirm_password(self.conn, user, "wrong wrong wrong", now=NOW)
        with self.assertRaises(TooMany):
            auth.confirm_password(self.conn, user, PASSWORD, now=NOW)

    def test_delete_cascades_every_row_of_the_user_and_nothing_else(self) -> None:
        db.seed(self.conn)
        user, _ = self.register("asha")
        keeper, _ = self.register("ravi")
        item = self.conn.execute("SELECT id FROM items WHERE track = 'dsa' LIMIT 1").fetchone()["id"]
        for u in (user["id"], keeper["id"]):
            self.conn.execute("INSERT INTO attempts (user_id, item_id, on_date, mode) VALUES (?,?,?,?)", (u, item, "2026-10-12", "solve"))
            self.conn.execute("INSERT INTO reviews (user_id, item_id, kind, due_date) VALUES (?,?,?,?)", (u, item, "recall", "2026-10-13"))
            self.conn.execute("INSERT INTO decisions (user_id, item_id, chose, on_date) VALUES (?,?,?,?)", (u, item, "x", "2026-10-12"))
            self.conn.execute("INSERT INTO user_items (user_id, item_id, starred) VALUES (?,?,1)", (u, item))
            self.conn.execute(
                "INSERT INTO reset_snapshots (user_id, scope, mark, payload, created_at) VALUES (?,?,?,?,?)",
                (u, "all", "[]", "{}", "2026-10-12T00:00:00+00:00"),
            )
        self.conn.commit()

        with self.assertRaises(Forbidden):
            auth.delete_account(self.conn, user, "wrong wrong wrong", now=NOW)
        self.assertEqual(self.count("SELECT COUNT(*) FROM users"), 2)

        auth.delete_account(self.conn, user, PASSWORD, now=NOW)

        for table in ("attempts", "reviews", "decisions", "user_items", "reset_snapshots", "auth_sessions"):
            self.assertEqual(self.count(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", user["id"]), 0, table)
            self.assertEqual(self.count(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", keeper["id"]), 1, table)
        self.assertEqual(self.count("SELECT COUNT(*) FROM users"), 1)
        self.assertGreater(self.count("SELECT COUNT(*) FROM items"), 0, "curriculum is shared and stays")

    def test_admin_reset_password_prints_a_working_one_time_password(self) -> None:
        user, token = self.register()
        fresh = auth.admin_reset_password(self.conn, "asha")
        self.assertGreaterEqual(len(fresh), auth.PASSWORD_MIN)
        self.assertIsNone(auth.resolve_session(self.conn, token, NOW))
        auth.login(self.conn, "asha", fresh, now=NOW)
        with self.assertRaises(Invalid):
            auth.admin_reset_password(self.conn, "nobody")

    def test_corrupt_stored_hash_is_a_loud_value_error(self) -> None:
        with self.assertRaises(ValueError):
            auth.verify_password(PASSWORD, "scrypt$nonsense")
        with self.assertRaises(ValueError):
            auth.verify_password(PASSWORD, f"scrypt${2**30}$8$1$AAAA$AAAA")

    def test_log_lines_never_carry_secrets(self) -> None:
        with mock.patch("builtins.print") as out:
            user, token = self.register()
            with self.assertRaises(Unauthorized):
                auth.login(self.conn, "asha\nforged line", "wrong password!", now=NOW)
        text = "\n".join(str(call.args[0]) for call in out.call_args_list)
        for secret in (PASSWORD, token, user["password_hash"], "wrong password!"):
            self.assertNotIn(secret, text)
        self.assertEqual(len(text.splitlines()), 2, "a newline in a username cannot forge a log line")


if __name__ == "__main__":
    unittest.main()
