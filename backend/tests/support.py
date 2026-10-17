"""Shared test fixtures: a seeded database and quick account rows (no scrypt cost)."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from unittest import mock

from app import db
from app.services import core

SEED = Path(__file__).resolve().parent.parent / "seed"
HASH = "scrypt$16384$8$1$AAAAAAAAAAAAAAAAAAAAAA==$AAAA"  # never verified in these tests


def new_user(conn, name: str = "asha", **fields) -> dict:
    values = {"preferred_list": "plan", "timezone": "Asia/Kolkata", **fields}
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, preferred_list, timezone, created_at, weekly_sessions, "
        "design_sessions, design_minutes) VALUES (?,?,?,?,?,?,?,?)",
        (name, HASH, values["preferred_list"], values["timezone"], "2026-10-01T00:00:00+00:00",
         values.get("weekly_sessions", 5), values.get("design_sessions", 3), values.get("design_minutes", 30)),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone())


class SeededTest(unittest.TestCase):
    """A real seeded SQLite file in a temp dir and one account, `self.user`."""

    user_fields: dict = {}
    quiet_logs = True

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "prep.db"
        db.SEED_DIR = SEED
        self.conn = db.connect()
        db.init(self.conn)
        db.seed(self.conn)
        self.user = new_user(self.conn, **self.user_fields)
        if self.quiet_logs:  # services log decisions; keep test output readable
            quiet = mock.patch("builtins.print")
            quiet.start()
            self.addCleanup(quiet.stop)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def count(self, sql: str, *params) -> int:
        return self.conn.execute(sql, params).fetchone()[0]

    @contextmanager
    def on(self, day: date):
        """Run the block as if today were `day` in every user's timezone."""
        with mock.patch.object(core, "today_in_tz", return_value=day):
            yield

    def twin(self, tracks: tuple[str, ...], missing_from: tuple[str, ...] = ()) -> list[dict]:
        """One item per track in `tracks`, all the same problem (slug), and the problem in
        none of `missing_from`. Rows come back in the order of `tracks`."""
        marks = ",".join("?" for _ in tracks)
        absent = " AND ".join("slug NOT IN (SELECT slug FROM items WHERE track = ? AND slug IS NOT NULL)" for _ in missing_from)
        sql = (
            f"SELECT slug FROM items WHERE track IN ({marks}) AND slug IS NOT NULL "
            + (f"AND {absent} " if absent else "")
            + f"GROUP BY slug HAVING COUNT(DISTINCT track) = {len(tracks)} ORDER BY MIN(seq) LIMIT 1"
        )
        slug = self.conn.execute(sql, (*tracks, *missing_from)).fetchone()["slug"]
        return [
            dict(self.conn.execute("SELECT * FROM items WHERE track = ? AND slug = ? ORDER BY seq LIMIT 1", (t, slug)).fetchone())
            for t in tracks
        ]
