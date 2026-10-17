"""Spreading an overdue backlog across the coming days. Run: .venv/bin/python -m unittest -v"""

from __future__ import annotations

import unittest
from collections import Counter
from datetime import timedelta

from app.errors import Invalid
from app.services import core, items

from .support import SeededTest, new_user


class SpreadTest(SeededTest):
    def setUp(self) -> None:
        super().setUp()
        self.today = core.today_in_tz(self.user)
        self.item = self.conn.execute("SELECT id FROM items WHERE track = 'dsa' ORDER BY seq LIMIT 1").fetchone()["id"]

    def review(self, days_from_today: int, done: bool = False) -> None:
        due = (self.today + timedelta(days=days_from_today)).isoformat()
        self.conn.execute(
            "INSERT INTO reviews (user_id, item_id, kind, due_date, done_date, outcome) VALUES (?,?,?,?,?,?)",
            (self.user["id"], self.item, "recall", due, due if done else None, "pass" if done else None),
        )
        self.conn.commit()

    def open_due_dates(self) -> Counter:
        return Counter(
            r["due_date"] for r in self.conn.execute("SELECT due_date FROM reviews WHERE user_id = ? AND done_date IS NULL", (self.user["id"],))
        )

    def day(self, n: int) -> str:
        return (self.today + timedelta(days=n)).isoformat()

    def test_overdue_reviews_fill_days_from_today_up_to_the_cap(self) -> None:
        for late in (12, 12, 10, 6, 6, 3, 1):
            self.review(-late)
        result = items.spread_overdue(self.conn, self.user, per_day=3)
        self.assertEqual(result["moved"], 7)
        self.assertEqual(self.open_due_dates(), Counter({self.day(0): 3, self.day(1): 3, self.day(2): 1}))

    def test_days_that_already_have_reviews_take_fewer(self) -> None:
        self.review(0)
        self.review(0)
        self.review(1)
        for _ in range(4):
            self.review(-5)
        items.spread_overdue(self.conn, self.user, per_day=3)
        self.assertEqual(self.open_due_dates(), Counter({self.day(0): 3, self.day(1): 3, self.day(2): 1}))

    def test_oldest_overdue_comes_back_first(self) -> None:
        self.review(-2)
        self.review(-9)
        items.spread_overdue(self.conn, self.user, per_day=1)
        rows = self.conn.execute("SELECT id, due_date FROM reviews ORDER BY id").fetchall()
        # The review that was 9 days late gets today; the 2-day one tomorrow.
        self.assertEqual([r["due_date"] for r in rows], [self.day(1), self.day(0)])

    def test_completed_and_future_reviews_are_untouched(self) -> None:
        self.review(-4, done=True)
        self.review(3)
        self.assertEqual(items.spread_overdue(self.conn, self.user)["moved"], 0)
        done = self.conn.execute("SELECT due_date FROM reviews WHERE done_date IS NOT NULL").fetchone()["due_date"]
        self.assertEqual(done, self.day(-4))
        self.assertEqual(self.open_due_dates(), Counter({self.day(3): 1}))

    def test_another_users_reviews_are_not_moved(self) -> None:
        other = new_user(self.conn, "ravi")
        self.conn.execute(
            "INSERT INTO reviews (user_id, item_id, kind, due_date) VALUES (?,?,?,?)",
            (other["id"], self.item, "recall", self.day(-5)),
        )
        self.conn.commit()
        self.review(-2)
        self.assertEqual(items.spread_overdue(self.conn, self.user)["moved"], 1)
        left = self.conn.execute("SELECT due_date FROM reviews WHERE user_id = ?", (other["id"],)).fetchone()[0]
        self.assertEqual(left, self.day(-5))

    def test_cap_must_be_positive(self) -> None:
        with self.assertRaises(Invalid):
            items.spread_overdue(self.conn, self.user, per_day=0)


if __name__ == "__main__":
    unittest.main()
