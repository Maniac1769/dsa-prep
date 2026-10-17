"""The operator commands: python -m app.admin reset-password|delete-user."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone

from app import admin, auth, db
from app.errors import Unauthorized

from .support import SeededTest

NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


class AdminTest(SeededTest):
    quiet_logs = False

    def run_admin(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = admin.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    @staticmethod
    def password_in(out: str) -> str:
        line = next(l for l in out.splitlines() if l.startswith("One-time password for"))
        return line.split(": ", 1)[1]

    def test_reset_password_prints_a_one_time_password_that_works(self) -> None:
        user, token = auth.register(self.conn, "ravi", "an old passphrase", "UTC", now=NOW)
        code, out, _ = self.run_admin("reset-password", "ravi")
        self.assertEqual(code, 0)
        password = self.password_in(out)
        self.assertGreaterEqual(len(password), auth.PASSWORD_MIN)
        self.assertIsNone(auth.resolve_session(self.conn, token, NOW), "signed out everywhere")
        auth.login(self.conn, "ravi", password, now=NOW)
        with self.assertRaises(Unauthorized):
            auth.login(self.conn, "ravi", "an old passphrase", now=NOW)

    def test_two_resets_print_different_passwords(self) -> None:
        auth.register(self.conn, "ravi", "an old passphrase", "UTC", now=NOW)
        first = self.password_in(self.run_admin("reset-password", "ravi")[1])
        second = self.password_in(self.run_admin("reset-password", "ravi")[1])
        self.assertNotEqual(first, second)

    def test_delete_user_removes_the_account_and_its_data(self) -> None:
        user, _ = auth.register(self.conn, "ravi", "an old passphrase", "UTC", now=NOW)
        item = self.conn.execute("SELECT id FROM items LIMIT 1").fetchone()["id"]
        self.conn.execute("INSERT INTO attempts (user_id, item_id, on_date, mode) VALUES (?,?,?,?)", (user["id"], item, "2026-10-12", "solve"))
        self.conn.commit()
        code, out, _ = self.run_admin("delete-user", "RAVI")
        self.assertEqual(code, 0)
        self.assertIn("Deleted ravi", out)
        self.assertEqual(self.count("SELECT COUNT(*) FROM users WHERE username = 'ravi'"), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE user_id = ?", user["id"]), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM users"), 1, "the other account is untouched")

    def test_unknown_user_is_an_error_not_a_crash(self) -> None:
        for command in ("reset-password", "delete-user"):
            code, out, err = self.run_admin(command, "ghost")
            self.assertEqual(code, 1, command)
            self.assertNotIn("password for", out)
            self.assertIn("ghost", err)


if __name__ == "__main__":
    unittest.main()
