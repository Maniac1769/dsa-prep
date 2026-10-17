"""The weekly session model: the kind follows the count of full sessions, never the weekday."""

from __future__ import annotations

import unittest
from datetime import date, timedelta

from app.services import account, core, items, plan, sessions, stats, today

from .support import SeededTest

MONDAY = date(2026, 10, 12)


def day(n: int) -> date:
    return MONDAY + timedelta(days=n)


class SessionKindTest(SeededTest):
    def next_item(self) -> int:
        rows = core.preferred_pool(core.items_for(self.conn, self.user["id"], core.DSA_GROUP), self.user)
        return core.next_new_from(rows)["id"]

    def full_session(self, d: date, mode: str = "solve") -> None:
        with self.on(d):
            items.log_attempt(self.conn, self.user, self.next_item(), mode, 2, 30, "", None)

    def view(self, d: date) -> dict:
        with self.on(d):
            return today.today(self.conn, self.user)

    def test_kind_follows_the_sequence_for_every_weekly_budget(self) -> None:
        for n, seq in sessions.SEQUENCES.items():
            self.conn.execute("DELETE FROM attempts")
            self.conn.execute("DELETE FROM reviews")
            account.update_settings(self.conn, self.user, {"weekly_sessions": n})
            for i, expected in enumerate(seq):
                t = self.view(day(i))
                self.assertEqual((t["session"]["kind"], t["session"]["number"], t["session"]["of"]), (expected, i + 1, n), f"{n} sessions, #{i + 1}")
                self.full_session(day(i))
            self.assertTrue(self.view(day(n - 1))["session"]["week_done"])

    def test_a_day_with_a_full_session_keeps_that_days_kind(self) -> None:
        for i in range(3):
            self.full_session(day(i))
        before = self.view(day(3))["session"]
        self.assertEqual((before["kind"], before["number"], before["done_today"]), ("resolve", 4, False))
        self.full_session(day(3), mode="resolve")
        after = self.view(day(3))["session"]
        self.assertEqual((after["kind"], after["number"], after["done_today"]), ("resolve", 4, True))

    def test_a_lost_day_shifts_nothing_and_never_doubles_up(self) -> None:
        self.full_session(day(0))
        self.full_session(day(2))  # Tuesday lost
        t = self.view(day(3))
        self.assertEqual((t["session"]["kind"], t["session"]["number"]), ("learn", 3))
        self.assertEqual(t["day"]["headline"], "Learn and solve")
        # Saturday after a week with only two sessions is still just the next learn session.
        self.assertEqual(self.view(day(5))["session"]["kind"], "learn")

    def test_past_the_budget_the_week_repeats_learn_and_is_done(self) -> None:
        for i in range(5):
            self.full_session(day(i))
        t = self.view(day(5))
        self.assertEqual((t["session"]["kind"], t["session"]["number"], t["session"]["week_done"]), ("learn", 6, True))

    def test_the_count_restarts_every_monday(self) -> None:
        for i in range(5):
            self.full_session(day(i))
        t = self.view(day(7))
        self.assertEqual((t["session"]["kind"], t["session"]["number"], t["session"]["week_done"]), ("learn", 1, False))

    def test_a_recall_only_day_is_a_short_day_and_does_not_count(self) -> None:
        first = self.next_item()
        with self.on(day(0)):
            items.log_attempt(self.conn, self.user, first, "solve", 2, None, "", None)
        with self.on(day(1)):
            items.log_attempt(self.conn, self.user, first, "recall", 3, 5, "", None)
        t = self.view(day(1))
        self.assertEqual((t["session"]["done_today"], t["session"]["short_days"], t["session"]["number"]), (False, 1, 2))
        self.assertEqual(sessions.week_state(self.conn, self.user, day(1)).full_count, 1)
        # A recall review completed that day is a recall attempt too.
        self.assertEqual(self.view(day(2))["session"]["number"], 2)

    def test_a_full_day_with_a_recall_still_counts_once(self) -> None:
        first = self.next_item()
        with self.on(day(0)):
            items.log_attempt(self.conn, self.user, first, "recall", 3, None, "", None)
            items.log_attempt(self.conn, self.user, first, "learn", 1, None, "", None)
        t = self.view(day(0))
        self.assertEqual((t["session"]["done_today"], t["session"]["short_days"], t["session"]["number"]), (True, 0, 1))

    def test_a_design_attempt_is_not_a_dsa_session(self) -> None:
        lld = self.conn.execute("SELECT id FROM items WHERE track = 'lld' ORDER BY seq LIMIT 1").fetchone()["id"]
        with self.on(day(0)):
            items.log_attempt(self.conn, self.user, lld, "learn", 2, 30, "", None)
        t = self.view(day(0))
        self.assertEqual((t["session"]["done_today"], t["session"]["number"]), (False, 1))
        self.assertEqual(t["design"]["sessions_done"], 1)

    def test_design_is_offered_until_the_weekly_design_budget_is_met(self) -> None:
        account.update_settings(self.conn, self.user, {"design_sessions": 2, "design_minutes": 45})
        t = self.view(day(0))
        self.assertEqual((t["design"]["sessions_done"], t["design"]["sessions_target"], t["design"]["minutes"]), (0, 2, 45))
        for i in range(2):
            lld = self.conn.execute(
                "SELECT id FROM items WHERE track = 'lld' ORDER BY seq LIMIT 1 OFFSET ?", (i,)).fetchone()["id"]
            with self.on(day(i)):
                items.log_attempt(self.conn, self.user, lld, "learn", 2, 30, "", None)
        self.assertIsNone(self.view(day(2))["design"])
        self.assertIsNotNone(self.view(day(7))["design"], "a new week offers it again")

    def test_no_design_when_the_budget_is_zero(self) -> None:
        account.update_settings(self.conn, self.user, {"design_sessions": 0})
        self.assertIsNone(self.view(day(0))["design"])

    def test_weeks_start_on_monday(self) -> None:
        self.full_session(day(6))  # Sunday
        self.assertEqual(self.view(day(6))["session"]["number"], 1)
        self.assertEqual(sessions.week_state(self.conn, self.user, day(6)).monday, MONDAY)
        self.assertEqual(sessions.week_state(self.conn, self.user, day(7)).monday, day(7))

    def test_new_work_blocked_makes_a_review_session_whatever_its_kind(self) -> None:
        item = self.next_item()
        for _ in range(7):  # more than the cap of 6 anchor re-solves due
            self.conn.execute(
                "INSERT INTO reviews (user_id, item_id, kind, due_date) VALUES (?,?,?,?)",
                (self.user["id"], item, "full_solve", day(-3).isoformat()),
            )
        self.conn.commit()
        t = self.view(day(0))
        self.assertEqual(t["session"]["kind"], "learn")
        self.assertFalse(t["verdict"]["allow_new_work"])
        self.assertIsNone(t["focus"])
        self.assertEqual(t["day"]["headline"], "Review session")
        self.assertEqual(t["day"]["guidance"], t["verdict"]["reason"])


class ShortDayAndQuietTest(SeededTest):
    def log(self, d: date, item_id: int, mode: str = "solve") -> None:
        with self.on(d):
            items.log_attempt(self.conn, self.user, item_id, mode, 2, None, "", None)

    def first_items(self, n: int) -> list[int]:
        return [r["id"] for r in self.conn.execute(
            "SELECT id FROM items WHERE track = 'dsa' AND block != 'cf' ORDER BY seq LIMIT ?", (n,))]

    def test_quiet_days_appear_after_two_days_and_never_before_the_first_attempt(self) -> None:
        with self.on(day(0)):
            self.assertIsNone(today.today(self.conn, self.user)["quiet_days"])
        self.log(day(0), self.first_items(1)[0])
        for offset, expected in ((0, None), (1, None), (2, 2), (5, 5)):
            with self.on(day(offset)):
                self.assertEqual(today.today(self.conn, self.user)["quiet_days"], expected, offset)

    def test_a_short_day_ends_the_quiet_spell(self) -> None:
        item = self.first_items(1)[0]
        self.log(day(0), item)
        self.log(day(3), item, mode="recall")
        with self.on(day(3)):
            self.assertIsNone(today.today(self.conn, self.user)["quiet_days"])

    def test_short_day_offers_up_to_two_due_recalls(self) -> None:
        ids = self.first_items(3)
        for item in ids:
            self.log(day(0), item)
        with self.on(day(1)):
            t = today.today(self.conn, self.user)
        self.assertEqual(len(t["reviews"]), 3)
        self.assertEqual(len(t["short_day"]["reviews"]), 2)
        self.assertTrue(all(r["kind"] == "recall" for r in t["short_day"]["reviews"]))
        self.assertIsNone(t["short_day"]["recall_item"])

    def test_short_day_falls_back_to_the_most_recent_problem_from_an_earlier_day(self) -> None:
        first, second = self.first_items(2)
        self.log(day(0), first)
        with self.on(day(1)):
            for r in core.due_reviews(self.conn, self.user["id"], day(1), core.DSA_GROUP):
                items.complete_review(self.conn, self.user, r["id"], "pass", "")
        self.log(day(2), second)  # studied today: recalling it minutes later proves nothing
        with self.on(day(2)):
            sd = today.today(self.conn, self.user)["short_day"]
        self.assertEqual(sd["reviews"], [])
        self.assertEqual(sd["recall_item"]["id"], first)

    def test_short_day_offers_nothing_when_everything_was_studied_today(self) -> None:
        first, second = self.first_items(2)
        self.log(day(0), first)
        self.log(day(0), second)
        with self.on(day(0)):
            self.assertIsNone(today.today(self.conn, self.user)["short_day"]["recall_item"])

    def test_short_day_is_empty_for_a_new_account(self) -> None:
        with self.on(day(0)):
            self.assertEqual(today.today(self.conn, self.user)["short_day"], {"reviews": [], "recall_item": None})


class PlanAndStatsTest(SeededTest):
    def test_plan_lists_the_weeks_sessions_with_done_and_next(self) -> None:
        for i in range(2):
            first = core.next_new_from(core.preferred_pool(core.items_for(self.conn, self.user["id"], core.DSA_GROUP), self.user))
            with self.on(day(i)):
                items.log_attempt(self.conn, self.user, first["id"], "solve", 2, None, "", None)
        with self.on(day(2)):
            p = plan.plan(self.conn, self.user)
        self.assertEqual([s["kind"] for s in p["sessions"]], ["learn", "learn", "learn", "resolve", "mixed"])
        self.assertEqual([s["done"] for s in p["sessions"]], [True, True, False, False, False])
        self.assertEqual([s["next"] for s in p["sessions"]], [False, False, True, False, False])
        self.assertEqual((p["weekly_sessions"], p["design_sessions"], p["design_minutes"]), (5, 3, 30))
        self.assertEqual(p["pace"]["new_per_week"], 3)
        self.assertNotIn("week", p)
        self.assertEqual(p["total_minutes"], 5 * 60 + 3 * 30)

    def test_pace_follows_the_learn_sessions_in_the_week(self) -> None:
        for n, learn in ((3, 2), (4, 3), (5, 3), (6, 4), (7, 4)):
            account.update_settings(self.conn, self.user, {"weekly_sessions": n})
            with self.on(day(0)):
                self.assertEqual(plan.plan(self.conn, self.user)["pace"]["new_per_week"], learn, n)

    def test_each_list_has_its_own_roadmap_shape(self) -> None:
        with self.on(day(0)):
            roadmap = plan.plan(self.conn, self.user)["roadmap"]
            self.assertIn("group", roadmap[0])
            account.update_settings(self.conn, self.user, {"preferred_list": "a2z"})
            roadmap = plan.plan(self.conn, self.user)["roadmap"]
            self.assertEqual((len(roadmap), roadmap[0]["state"], set(roadmap[0]) >= {"title", "no", "done", "total"}), (20, "current", True))

    def test_stats_report_sessions_this_week(self) -> None:
        first = core.next_new_from(core.preferred_pool(core.items_for(self.conn, self.user["id"], core.DSA_GROUP), self.user))
        with self.on(day(0)):
            items.log_attempt(self.conn, self.user, first["id"], "solve", 2, 30, "", None)
            kpi = stats.stats(self.conn, self.user)["kpi"]
        self.assertEqual((kpi["sessions_week"], kpi["sessions_target"]), (1, 5))
        self.assertEqual(kpi["unaided"], 1)


if __name__ == "__main__":
    unittest.main()
