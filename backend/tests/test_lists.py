"""Three lists, one record per problem: canonical logging, switching lists, ladder eligibility."""

from __future__ import annotations

import unittest

from app.errors import Invalid
from app.services import account, core, items, problems, reset, stats, today

from .support import SeededTest


class CanonicalRecordTest(SeededTest):
    def attempts_on(self, item_id: int) -> int:
        return self.count("SELECT COUNT(*) FROM attempts WHERE user_id = ? AND item_id = ?", self.user["id"], item_id)

    def test_logging_an_sde_row_with_a_plan_twin_writes_to_the_plan_item(self) -> None:
        plan_item, sde_item = self.twin(("dsa", "sde"))
        items.log_attempt(self.conn, self.user, sde_item["id"], "solve", 3, None, "", None)
        self.assertEqual(self.attempts_on(plan_item["id"]), 1)
        self.assertEqual(self.attempts_on(sde_item["id"]), 0)
        # Both rows show the one status, and the sheet row points at the item that was logged.
        row = next(r for s in problems.problems(self.conn, self.user, "sde")["steps"]
                   for lec in s["lectures"] for r in lec["rows"] if r["id"] == sde_item["id"])
        self.assertEqual((row["status"], row["log_id"], row["plan_block"]), ("solid", plan_item["id"], plan_item["block"]))
        plan_row = next(r for g in problems.problems(self.conn, self.user, "plan")["groups"]
                        for b in g["blocks"] for r in b["rows"] if r["id"] == plan_item["id"])
        self.assertEqual(plan_row["status"], "solid")

    def test_logging_an_a2z_row_with_a_plan_twin_writes_to_the_plan_item(self) -> None:
        plan_item, a2z_item = self.twin(("dsa", "a2z"))
        items.log_attempt(self.conn, self.user, a2z_item["id"], "solve", 2, None, "", None)
        self.assertEqual(self.attempts_on(plan_item["id"]), 1)
        self.assertEqual(self.attempts_on(a2z_item["id"]), 0)

    def test_sde_beats_a2z_when_the_plan_does_not_have_the_problem(self) -> None:
        sde_item, a2z_item = self.twin(("sde", "a2z"), missing_from=("dsa",))
        items.log_attempt(self.conn, self.user, a2z_item["id"], "solve", 2, None, "", None)
        self.assertEqual(self.attempts_on(sde_item["id"]), 1)
        self.assertEqual(self.attempts_on(a2z_item["id"]), 0)

    def test_starring_and_resetting_act_on_the_canonical_item(self) -> None:
        plan_item, sde_item = self.twin(("dsa", "sde"))
        items.log_attempt(self.conn, self.user, sde_item["id"], "solve", 2, None, "", None)
        self.assertEqual(items.toggle_star(self.conn, self.user, sde_item["id"])["id"], plan_item["id"])
        self.assertTrue(items.item_detail(self.conn, self.user, plan_item["id"])["item"]["starred"])
        reset.reset(self.conn, self.user, "item", sde_item["id"])
        self.assertEqual(self.attempts_on(plan_item["id"]), 0)

    def test_resetting_a_sheet_clears_the_records_it_shares_with_the_plan(self) -> None:
        plan_item, sde_item = self.twin(("dsa", "sde"))
        items.log_attempt(self.conn, self.user, plan_item["id"], "solve", 2, None, "", None)
        self.assertEqual(reset.reset_preview(self.conn, self.user)["scopes"]["sde"]["attempts"], 1)
        reset.reset(self.conn, self.user, "sde")
        self.assertEqual(self.attempts_on(plan_item["id"]), 0)

    def test_a_problem_without_a_slug_is_its_own_record(self) -> None:
        row = self.conn.execute(
            "SELECT id FROM items WHERE track IN ('a2z','sde') AND slug IS NULL ORDER BY seq LIMIT 1"
        ).fetchone()
        items.log_attempt(self.conn, self.user, row["id"], "learn", 1, None, "", None)
        self.assertEqual(self.attempts_on(row["id"]), 1)

    def test_only_listed_problems_can_be_starred(self) -> None:
        lld = self.conn.execute("SELECT id FROM items WHERE track = 'lld' LIMIT 1").fetchone()["id"]
        with self.assertRaises(Invalid):
            items.toggle_star(self.conn, self.user, lld)


class SwitchingListsTest(SeededTest):
    def solid(self, key: str) -> int:
        return next(i for i in account.account_lists(self.conn, self.user)["lists"] if i["key"] == key)["solid"]

    def test_switching_preferred_list_keeps_progress(self) -> None:
        plan_item, sde_item = self.twin(("dsa", "sde"))
        items.log_attempt(self.conn, self.user, plan_item["id"], "solve", 3, None, "", None)
        before = self.count("SELECT COUNT(*) FROM attempts")
        reviews = self.count("SELECT COUNT(*) FROM reviews")

        account.update_settings(self.conn, self.user, {"preferred_list": "sde"})

        self.assertEqual(self.count("SELECT COUNT(*) FROM attempts"), before)
        self.assertEqual(self.count("SELECT COUNT(*) FROM reviews"), reviews)
        self.assertEqual(self.solid("plan"), 1)
        self.assertEqual(self.solid("sde"), 1, "the shared problem counts in the new list too")
        t = today.today(self.conn, self.user)
        self.assertEqual((t["list"]["key"], t["unaided"]), ("sde", 1))
        self.assertEqual(stats.stats(self.conn, self.user)["bars"][0]["solid"], 1)

        account.update_settings(self.conn, self.user, {"preferred_list": "plan"})
        self.assertEqual(self.solid("plan"), 1)

    def test_the_new_list_continues_after_what_is_already_studied(self) -> None:
        plan_item, sde_item = self.twin(("dsa", "sde"))
        account.update_settings(self.conn, self.user, {"preferred_list": "sde"})
        first = today.today(self.conn, self.user)["focus"]["id"]
        sde_first = self.conn.execute("SELECT id FROM items WHERE track = 'sde' ORDER BY seq LIMIT 1").fetchone()["id"]
        self.assertEqual(first, sde_first)
        items.log_attempt(self.conn, self.user, sde_first, "solve", 2, None, "", None)
        self.assertNotEqual(today.today(self.conn, self.user)["focus"]["id"], sde_first)

    def test_only_the_preferred_list_gets_a_completion_bar(self) -> None:
        for key, label in (("plan", "Prep plan"), ("sde", "Striver SDE sheet"), ("a2z", "Striver A2Z sheet")):
            account.update_settings(self.conn, self.user, {"preferred_list": key})
            self.assertEqual([b["label"] for b in stats.stats(self.conn, self.user)["bars"]], [label, "LLD", "HLD"])

    def test_settings_validate_and_apply_only_what_was_sent(self) -> None:
        account.update_settings(self.conn, self.user, {"weekly_sessions": 4})
        self.assertEqual(self.user["design_sessions"], 3)
        for bad in ({"preferred_list": "x"}, {"timezone": "Nope/Zone"}, {"weekly_sessions": 2}, {"weekly_sessions": 8},
                    {"design_sessions": 8}, {"design_minutes": 20}, {"password_hash": "x"}):
            with self.assertRaises(Invalid, msg=str(bad)):
                account.update_settings(self.conn, self.user, bad)


class LadderEligibilityTest(SeededTest):
    def kinds(self, item_id: int) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT kind FROM reviews WHERE user_id = ? AND item_id = ? ORDER BY due_date", (self.user["id"], item_id))]

    def prefer(self, key: str) -> None:
        account.update_settings(self.conn, self.user, {"preferred_list": key})

    def test_preferred_list_problems_get_the_ladder_others_only_when_starred(self) -> None:
        a2z_only = self.twin(("a2z",), missing_from=("dsa", "sde"))[0]
        items.log_attempt(self.conn, self.user, a2z_only["id"], "solve", 2, None, "", None)
        self.assertEqual(self.kinds(a2z_only["id"]), [], "plan is preferred; an A2Z-only problem is not on the ladder")
        items.toggle_star(self.conn, self.user, a2z_only["id"])
        self.assertTrue(self.kinds(a2z_only["id"]))
        items.toggle_star(self.conn, self.user, a2z_only["id"])
        self.assertEqual(self.kinds(a2z_only["id"]), [])

        self.prefer("a2z")
        other = self.conn.execute(
            "SELECT id FROM items WHERE track = 'a2z' AND slug IS NOT NULL AND id != ? AND slug NOT IN "
            "(SELECT slug FROM items WHERE track IN ('dsa','sde') AND slug IS NOT NULL) ORDER BY seq LIMIT 1 OFFSET 5",
            (a2z_only["id"],),
        ).fetchone()["id"]
        items.log_attempt(self.conn, self.user, other, "solve", 2, None, "", None)
        self.assertTrue(self.kinds(other), "now A2Z is the preferred list")

    def test_a_plan_only_problem_is_not_on_the_ladder_when_a2z_is_preferred(self) -> None:
        self.prefer("a2z")
        plan_only = self.conn.execute(
            "SELECT id FROM items WHERE track = 'dsa' AND block != 'cf' AND (slug IS NULL OR slug NOT IN "
            "(SELECT slug FROM items WHERE track = 'a2z' AND slug IS NOT NULL)) ORDER BY seq LIMIT 1"
        ).fetchone()["id"]
        items.log_attempt(self.conn, self.user, plan_only, "solve", 2, None, "", None)
        self.assertEqual(self.kinds(plan_only), [])

    def test_unstarring_keeps_the_ladder_of_a_problem_in_the_preferred_list(self) -> None:
        first = self.conn.execute("SELECT id FROM items WHERE track = 'dsa' AND block != 'cf' ORDER BY seq LIMIT 1").fetchone()["id"]
        items.log_attempt(self.conn, self.user, first, "solve", 2, None, "", None)
        ladder = self.kinds(first)
        items.toggle_star(self.conn, self.user, first)
        items.toggle_star(self.conn, self.user, first)
        self.assertEqual(self.kinds(first), ladder)

    def test_the_first_problem_of_each_sde_step_gets_a_full_re_solve_the_rest_do_not(self) -> None:
        self.prefer("sde")
        first, second = (r["id"] for r in self.conn.execute("SELECT id FROM items WHERE track = 'sde' ORDER BY seq LIMIT 2"))
        items.log_attempt(self.conn, self.user, first, "solve", 2, None, "", None)
        items.log_attempt(self.conn, self.user, second, "solve", 2, None, "", None)
        record = core.item_by_id(self.conn, self.user["id"], first, canonical=True)["id"]
        record2 = core.item_by_id(self.conn, self.user["id"], second, canonical=True)["id"]
        self.assertIn("full_solve", self.kinds(record), "judged by the sde row even when the record is a plan item")
        self.assertNotIn("full_solve", self.kinds(record2))
        self.assertTrue(self.kinds(record2))

    def test_a_recall_never_lays_the_ladder_or_counts_as_study(self) -> None:
        first = self.conn.execute("SELECT id FROM items WHERE track = 'dsa' AND block != 'cf' ORDER BY seq LIMIT 1").fetchone()["id"]
        items.log_attempt(self.conn, self.user, first, "recall", 2, None, "", None)
        self.assertEqual(self.kinds(first), [])
        items.log_attempt(self.conn, self.user, first, "solve", 2, None, "", None)
        self.assertTrue(self.kinds(first), "the first real study still lays it")


if __name__ == "__main__":
    unittest.main()
