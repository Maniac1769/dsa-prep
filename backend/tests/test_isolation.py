"""One account must never read, log into, star, reset or undo another account's data."""

from __future__ import annotations

import unittest

from app.errors import Conflict, NotFound
from app.services import core, design, items, plan, problems, reset, stats, today

from .support import SeededTest, new_user


class TwoUsersTest(SeededTest):
    def setUp(self) -> None:
        super().setUp()
        self.a = self.user
        self.b = new_user(self.conn, "ravi")
        self.first, self.second = (
            r["id"] for r in self.conn.execute(
                "SELECT id FROM items WHERE track = 'dsa' AND block != 'cf' ORDER BY seq LIMIT 2"
            )
        )

    def rows(self, table: str, user: dict) -> int:
        return self.count(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", user["id"])

    def a_studies(self) -> None:
        items.log_attempt(self.conn, self.a, self.first, "solve", 3, 30, "mine", None)
        items.add_decision(self.conn, self.a, self.first, "heap", "sort", "n log k")
        items.toggle_star(self.conn, self.a, self.second)

    # --- reads ------------------------------------------------------------------------

    def test_reads_show_nothing_of_the_other_account(self) -> None:
        self.a_studies()
        t = today.today(self.conn, self.b)
        self.assertEqual((t["reviews"], t["unaided"], t["streak"], t["session"]["number"]), ([], 0, 0, 1))
        self.assertEqual(t["focus"]["id"], self.first, "B still starts at the first problem")
        self.assertIsNone(t["quiet_days"])
        self.assertEqual(t["short_day"], {"reviews": [], "recall_item": None})

        view = problems.problems(self.conn, self.b, "plan")
        self.assertEqual(view["solid"], 0)
        self.assertEqual(stats.stats(self.conn, self.b)["any_activity"], False)
        self.assertEqual(reset.reset_preview(self.conn, self.b)["scopes"]["all"], {"attempts": 0, "reviews": 0})

        detail = items.item_detail(self.conn, self.b, self.first)
        self.assertEqual((detail["attempts"], detail["reviews"], detail["decisions"]), ([], [], []))
        self.assertEqual(detail["item"]["status"], "todo")
        self.assertFalse(items.item_detail(self.conn, self.b, self.second)["item"]["starred"])
        self.assertEqual(plan.plan(self.conn, self.b)["sessions"][0]["done"], False)
        self.assertEqual(design.design(self.conn, self.b)["phases"][0]["done"], 0)

    def test_the_owner_still_sees_their_own_data(self) -> None:
        self.a_studies()
        detail = items.item_detail(self.conn, self.a, self.first)
        self.assertEqual(len(detail["attempts"]), 1)
        self.assertEqual(len(detail["decisions"]), 1)
        self.assertTrue(items.item_detail(self.conn, self.a, self.second)["item"]["starred"])

    # --- writes -----------------------------------------------------------------------

    def test_logging_never_lands_on_the_other_account(self) -> None:
        self.a_studies()
        items.log_attempt(self.conn, self.b, self.first, "solve", 1, None, "", None)
        self.assertEqual((self.rows("attempts", self.a), self.rows("attempts", self.b)), (1, 1))
        self.assertEqual(items.item_detail(self.conn, self.a, self.first)["item"]["status"], "solid")
        self.assertEqual(items.item_detail(self.conn, self.b, self.first)["item"]["status"], "helped")

    def test_starring_is_per_account(self) -> None:
        items.toggle_star(self.conn, self.a, self.second)
        self.assertFalse(items.item_detail(self.conn, self.b, self.second)["item"]["starred"])
        items.toggle_star(self.conn, self.b, self.second)
        items.toggle_star(self.conn, self.b, self.second)  # B stars then unstars
        self.assertTrue(items.item_detail(self.conn, self.a, self.second)["item"]["starred"])

    def test_a_review_id_from_another_account_is_not_found(self) -> None:
        self.a_studies()
        review_id = self.conn.execute("SELECT id FROM reviews WHERE user_id = ?", (self.a["id"],)).fetchone()[0]
        with self.assertRaises(NotFound):
            items.complete_review(self.conn, self.b, review_id, "pass", "")
        self.assertEqual(self.count("SELECT COUNT(*) FROM reviews WHERE id = ? AND done_date IS NULL", review_id), 1)
        items.complete_review(self.conn, self.a, review_id, "pass", "")

    def test_reset_only_clears_the_callers_rows(self) -> None:
        self.a_studies()
        items.log_attempt(self.conn, self.b, self.first, "solve", 2, None, "", None)
        for scope in ("week", "plan", "all"):
            reset.reset(self.conn, self.b, scope)
            self.assertEqual(self.rows("attempts", self.b), 0)
            self.assertEqual(self.rows("attempts", self.a), 1, scope)
            self.assertGreater(self.rows("reviews", self.a), 0, scope)
            self.assertEqual(self.rows("decisions", self.a), 1, scope)
            items.log_attempt(self.conn, self.b, self.first, "solve", 2, None, "", None)
        reset.reset(self.conn, self.b, "item", self.first)
        self.assertEqual(self.rows("attempts", self.a), 1)
        self.assertEqual(self.count("SELECT COUNT(*) FROM user_items WHERE user_id = ? AND starred = 1", self.a["id"]), 1)

    def test_undo_belongs_to_the_account_that_reset(self) -> None:
        self.a_studies()
        reset.reset(self.conn, self.a, "all")
        self.assertIsNone(reset.reset_preview(self.conn, self.b)["undo"])
        with self.assertRaises(Conflict):
            reset.undo_reset(self.conn, self.b)
        self.assertEqual(reset.reset_preview(self.conn, self.a)["undo"]["scope"], "all")

    def test_undo_restores_into_the_right_account_when_ids_were_reused(self) -> None:
        items.log_attempt(self.conn, self.a, self.first, "solve", 2, None, "", None)
        reset.reset(self.conn, self.a, "all")
        # A's rows are gone, so their ids are free for B's next inserts.
        items.log_attempt(self.conn, self.b, self.second, "solve", 2, None, "", None)
        reset.reset(self.conn, self.b, "item", self.second)
        items.log_attempt(self.conn, self.b, self.second, "solve", 3, None, "", None)

        reset.undo_reset(self.conn, self.a)

        self.assertEqual(self.rows("attempts", self.a), 1)
        self.assertEqual(self.rows("attempts", self.b), 1)
        self.assertEqual(items.item_detail(self.conn, self.b, self.second)["item"]["status"], "solid")
        self.assertEqual(items.item_detail(self.conn, self.a, self.first)["item"]["status"], "unaided")

    def test_a_reset_by_one_does_not_expire_the_others_undo(self) -> None:
        self.a_studies()
        reset.reset(self.conn, self.a, "all")
        items.log_attempt(self.conn, self.b, self.first, "solve", 2, None, "", None)
        self.assertEqual(reset.reset_preview(self.conn, self.a)["undo"]["scope"], "all")

    def test_decisions_are_per_account(self) -> None:
        items.add_decision(self.conn, self.a, self.first, "heap", "", "")
        self.assertEqual(items.item_detail(self.conn, self.b, self.first)["decisions"], [])

    def test_a_shared_unknown_item_id_is_not_found_for_everyone(self) -> None:
        for user in (self.a, self.b):
            with self.assertRaises(NotFound):
                items.item_detail(self.conn, user, 999_999)
            with self.assertRaises(NotFound):
                items.log_attempt(self.conn, user, 999_999, "solve", 1, None, "", None)
        self.assertEqual(core.today_in_tz(self.a), core.today_in_tz(self.b))


if __name__ == "__main__":
    unittest.main()
