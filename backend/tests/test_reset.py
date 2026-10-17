"""Reset and undo against a real seeded SQLite file. Run: .venv/bin/python -m unittest -v"""

from __future__ import annotations

import json
import unittest
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.errors import Conflict, Invalid, NotFound
from app.services import account, core, items, reset

from .support import SeededTest


class ResetTest(SeededTest):
    def setUp(self) -> None:
        super().setUp()
        self.today = core.today_in_tz(self.user)
        self.monday = self.today - timedelta(days=self.today.weekday())
        self.last_week = self.monday - timedelta(days=3)

    # --- helpers -------------------------------------------------------------

    def item(self, track: str, n: int = 0) -> int:
        return self.conn.execute(
            "SELECT id FROM items WHERE track = ? AND block != 'cf' ORDER BY seq LIMIT 1 OFFSET ?", (track, n)
        ).fetchone()["id"]

    def old_attempt(self, item_id: int) -> None:
        """An attempt and its review, both dated last week, as if logged then."""
        stamp = f"{self.last_week.isoformat()} 12:00:00"
        self.conn.execute(
            "INSERT INTO attempts (user_id, item_id, on_date, mode, score, independent, created_at) VALUES (?,?,?,?,?,?,?)",
            (self.user["id"], item_id, self.last_week.isoformat(), "solve", 2, 1, stamp),
        )
        self.conn.execute(
            "INSERT INTO reviews (user_id, item_id, kind, due_date, created_at) VALUES (?,?,?,?,?)",
            (self.user["id"], item_id, "recall", (self.last_week + timedelta(days=1)).isoformat(), stamp),
        )
        self.conn.commit()

    def started_on(self) -> str:
        return self.conn.execute("SELECT started_on FROM users WHERE id = ?", (self.user["id"],)).fetchone()[0]

    def utc_stamp(self, local: datetime) -> str:
        return local.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # --- week ---------------------------------------------------------------

    def test_week_reset_keeps_earlier_weeks(self) -> None:
        old, new = self.item("dsa", 0), self.item("dsa", 1)
        self.old_attempt(old)
        items.log_attempt(self.conn, self.user, new, "solve", 2, None, "", None)
        self.assertGreater(self.count("SELECT COUNT(*) FROM reviews WHERE item_id = ?", new), 0)

        reset.reset(self.conn, self.user, "week")

        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", old), 1)
        self.assertEqual(self.count("SELECT COUNT(*) FROM reviews WHERE item_id = ?", old), 1)
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", new), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM reviews WHERE item_id = ?", new), 0)

    def test_week_reset_reopens_review_completed_this_week(self) -> None:
        old = self.item("dsa", 0)
        self.old_attempt(old)
        review_id = self.conn.execute("SELECT id FROM reviews WHERE item_id = ?", (old,)).fetchone()["id"]
        items.complete_review(self.conn, self.user, review_id, "pass", "")
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", old), 2)

        reset.reset(self.conn, self.user, "week")

        row = self.conn.execute("SELECT done_date, outcome FROM reviews WHERE id = ?", (review_id,)).fetchone()
        self.assertIsNone(row["done_date"])
        self.assertIsNone(row["outcome"])
        # The recall attempt that completing the review inserted is gone, and so is
        # any follow-up review it scheduled.
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", old), 1)
        self.assertEqual(self.count("SELECT COUNT(*) FROM reviews WHERE item_id = ?", old), 1)

    def test_week_boundary_is_local_midnight_not_utc(self) -> None:
        tz = ZoneInfo(self.user["timezone"])
        midnight = datetime.combine(self.monday, time.min, tz)
        item_id = self.item("dsa", 0)
        for minutes, due in ((30, "after"), (-1, "before")):
            self.conn.execute(
                "INSERT INTO reviews (user_id, item_id, kind, due_date, created_at) VALUES (?,?,?,?,?)",
                (self.user["id"], item_id, "recall", due, self.utc_stamp(midnight + timedelta(minutes=minutes))),
            )
        self.conn.commit()

        reset.reset(self.conn, self.user, "week")

        left = [r["due_date"] for r in self.conn.execute("SELECT due_date FROM reviews WHERE item_id = ?", (item_id,))]
        self.assertEqual(left, ["before"])

    def test_started_on_follows_remaining_attempts(self) -> None:
        items.log_attempt(self.conn, self.user, self.item("dsa", 0), "solve", 2, None, "", None)
        reset.reset(self.conn, self.user, "week")
        self.assertEqual(self.started_on(), "")

        self.old_attempt(self.item("dsa", 1))
        items.log_attempt(self.conn, self.user, self.item("dsa", 2), "solve", 2, None, "", None)
        reset.reset(self.conn, self.user, "week")
        self.assertEqual(self.started_on(), self.last_week.isoformat())

    # --- tracks, items, everything ---------------------------------------------

    def test_track_reset_only_touches_that_track(self) -> None:
        dsa, lld = self.item("dsa"), self.item("lld")
        items.log_attempt(self.conn, self.user, dsa, "solve", 3, None, "", None)
        items.log_attempt(self.conn, self.user, lld, "learn", 2, None, "", None)
        items.add_decision(self.conn, self.user, lld, "composition", "", "")

        reset.reset(self.conn, self.user, "plan")

        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", dsa), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM reviews WHERE item_id = ?", dsa), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", lld), 1)
        self.assertEqual(self.count("SELECT COUNT(*) FROM decisions WHERE item_id = ?", lld), 1)

    def test_design_scope_covers_lld_hld_and_prep(self) -> None:
        for track in ("lld", "hld", "prep"):
            items.log_attempt(self.conn, self.user, self.item(track), "learn", 2, None, "", None)
        reset.reset(self.conn, self.user, "design")
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts"), 0)

    def test_a2z_reset_clears_stars(self) -> None:
        a2z = self.item("a2z", 5)
        items.toggle_star(self.conn, self.user, a2z)
        reset.reset(self.conn, self.user, "a2z")
        self.assertEqual(self.count("SELECT COUNT(*) FROM user_items WHERE starred = 1"), 0)

    def test_item_reset(self) -> None:
        a, b = self.item("dsa", 0), self.item("dsa", 1)
        items.log_attempt(self.conn, self.user, a, "solve", 1, None, "", None)
        items.log_attempt(self.conn, self.user, b, "solve", 1, None, "", None)
        reset.reset(self.conn, self.user, "item", a)
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", a), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts WHERE item_id = ?", b), 1)

    def test_item_scope_needs_an_existing_item(self) -> None:
        with self.assertRaises(Invalid):
            reset.reset(self.conn, self.user, "item")
        with self.assertRaises(NotFound):
            reset.reset(self.conn, self.user, "item", 999_999)

    def test_unknown_scope_is_rejected(self) -> None:
        with self.assertRaises(Invalid):
            reset.reset(self.conn, self.user, "month")

    def test_all_reset_keeps_account_settings_and_curriculum(self) -> None:
        item_rows = self.count("SELECT COUNT(*) FROM items")
        account.update_settings(self.conn, self.user, {"design_minutes": 45})
        items.log_attempt(self.conn, self.user, self.item("dsa"), "solve", 2, None, "", None)
        items.toggle_star(self.conn, self.user, self.item("a2z", 3))

        reset.reset(self.conn, self.user, "all")

        for table in ("attempts", "reviews", "decisions"):
            self.assertEqual(self.count(f"SELECT COUNT(*) FROM {table}"), 0, table)
        self.assertEqual(self.count("SELECT COUNT(*) FROM user_items WHERE starred = 1"), 0)
        self.assertEqual(self.count("SELECT COUNT(*) FROM items"), item_rows)
        self.assertEqual(self.conn.execute("SELECT design_minutes FROM users").fetchone()[0], 45)

    # --- preview and undo ----------------------------------------------------------

    def test_preview_counts_what_each_scope_would_delete(self) -> None:
        self.old_attempt(self.item("dsa", 0))
        items.log_attempt(self.conn, self.user, self.item("dsa", 1), "solve", 2, None, "", None)
        preview = reset.reset_preview(self.conn, self.user)
        self.assertEqual(preview["scopes"]["week"]["attempts"], 1)
        self.assertEqual(preview["scopes"]["plan"]["attempts"], 2)
        self.assertEqual(preview["scopes"]["all"]["attempts"], 2)
        self.assertIsNone(preview["undo"])

    def test_undo_restores_the_snapshot_once(self) -> None:
        items.log_attempt(self.conn, self.user, self.item("dsa"), "solve", 2, None, "", None)
        result = reset.reset(self.conn, self.user, "all")
        self.assertTrue(result["snapshot"])
        self.assertEqual(reset.reset_preview(self.conn, self.user)["undo"]["scope"], "all")

        reset.undo_reset(self.conn, self.user)

        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts"), 1)
        self.assertGreater(self.count("SELECT COUNT(*) FROM reviews"), 0)
        self.assertIsNone(reset.reset_preview(self.conn, self.user)["undo"])
        with self.assertRaises(Conflict):
            reset.undo_reset(self.conn, self.user)

    def test_undo_is_refused_once_something_new_is_logged(self) -> None:
        items.log_attempt(self.conn, self.user, self.item("dsa", 0), "solve", 2, None, "", None)
        reset.reset(self.conn, self.user, "all")
        items.log_attempt(self.conn, self.user, self.item("dsa", 1), "solve", 2, None, "", None)

        self.assertIsNone(reset.reset_preview(self.conn, self.user)["undo"])
        with self.assertRaises(Conflict):
            reset.undo_reset(self.conn, self.user)

    def test_a_user_keeps_one_snapshot_however_often_they_reset(self) -> None:
        for _ in range(5):
            reset.reset(self.conn, self.user, "week")
        self.assertEqual(self.count("SELECT COUNT(*) FROM reset_snapshots"), 1)

    def test_snapshot_is_json_of_this_users_rows_only(self) -> None:
        items.log_attempt(self.conn, self.user, self.item("dsa"), "solve", 2, None, "", None)
        reset.reset(self.conn, self.user, "all")
        payload = json.loads(self.conn.execute("SELECT payload FROM reset_snapshots").fetchone()[0])
        self.assertEqual(len(payload["attempts"]), 1)
        self.assertGreater(len(payload["reviews"]), 0)

    def test_undo_restores_stars_and_started_on(self) -> None:
        items.toggle_star(self.conn, self.user, self.item("a2z", 3))
        items.log_attempt(self.conn, self.user, self.item("dsa"), "solve", 2, None, "", None)
        before = self.started_on()
        reset.reset(self.conn, self.user, "all")
        self.assertEqual(self.started_on(), "")
        reset.undo_reset(self.conn, self.user)
        self.assertEqual(self.started_on(), before)
        self.assertEqual(self.count("SELECT COUNT(*) FROM user_items WHERE starred = 1"), 1)


class StreakTest(unittest.TestCase):
    def test_best_streak_finds_the_longest_run(self) -> None:
        d = date(2026, 10, 1)
        days = {d, d + timedelta(1), d + timedelta(2), d + timedelta(5), d + timedelta(6)}
        self.assertEqual(core.longest_run(days), 3)
        self.assertEqual(core.longest_run(set()), 0)


if __name__ == "__main__":
    unittest.main()
