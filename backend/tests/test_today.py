"""Today before the first attempt, and when the session kind is not learn."""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from app.services import core, items, today

from .support import SeededTest


class FirstDayTest(SeededTest):
    def test_every_weekday_offers_the_first_problem_before_anything_is_logged(self) -> None:
        first = self.conn.execute(
            "SELECT id FROM items WHERE track = 'dsa' AND block != 'cf' ORDER BY seq LIMIT 1"
        ).fetchone()["id"]
        for day in range(12, 19):  # Monday 12 to Sunday 18 October 2026
            with mock.patch.object(core, "today_in_tz", return_value=date(2026, 10, day)):
                t = today.today(self.conn, self.user)
            self.assertIsNotNone(t["focus"], f"weekday {t['weekday']}")
            self.assertEqual(t["focus"]["id"], first)

    def test_a_session_that_is_not_learn_offers_no_new_problem(self) -> None:
        # Three learn sessions on Mon to Wed make Thursday the re-solve session.
        for day in (12, 13, 14):
            with mock.patch.object(core, "today_in_tz", return_value=date(2026, 10, day)):
                item = core.next_new_from(core.preferred_pool(core.items_for(self.conn, self.user["id"], core.DSA_GROUP), self.user))
                items.log_attempt(self.conn, self.user, item["id"], "solve", 2, None, "", None)
        with mock.patch.object(core, "today_in_tz", return_value=date(2026, 10, 15)):
            t = today.today(self.conn, self.user)
        self.assertEqual(t["session"]["kind"], "resolve")
        self.assertIsNone(t["focus"])


if __name__ == "__main__":
    unittest.main()
