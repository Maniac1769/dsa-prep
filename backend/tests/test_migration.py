"""The v2 (single-user) to v3 (accounts) migration, and seeding of the lists."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import db, lists

from . import legacy_v2_db as v2

SEED = Path(__file__).resolve().parent.parent / "seed"
PER_USER = ("users", "auth_sessions", "user_items", "reset_snapshots", "attempts", "reviews", "decisions")


class V2ToV3Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "prep.db"
        db.SEED_DIR = SEED
        conn = sqlite3.connect(db.DB_PATH)
        conn.executescript(db.V2_SCHEMA)
        conn.execute("PRAGMA user_version = 2")
        for i, track in enumerate(("dsa", "dsa", "lld", "a2z"), start=1):
            conn.execute(
                "INSERT INTO items (id, key, track, block, title, seq, starred, slug) VALUES (?,?,?,?,?,?,?,?)",
                (i * 10, f"{track}:{i}", track, str(i), f"Item {i}", i, 1 if track == "a2z" else 0, f"slug-{i}"),
            )
        conn.execute("INSERT INTO attempts (item_id, on_date, mode, score) VALUES (10, '2026-10-01', 'solve', 2)")
        conn.execute("INSERT INTO attempts (item_id, on_date, mode, score) VALUES (20, '2026-10-02', 'learn', 1)")
        conn.execute("INSERT INTO reviews (item_id, kind, due_date) VALUES (10, 'recall', '2026-10-02')")
        conn.execute("INSERT INTO decisions (item_id, chose, on_date) VALUES (30, 'composition', '2026-10-03')")
        conn.execute("INSERT INTO settings (key, value) VALUES ('timezone', 'Asia/Kolkata')")
        conn.commit()
        conn.close()
        self.conn = db.connect()

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def count(self, table: str) -> int:
        return self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    def test_copies_progress_into_legacy_tables_and_starts_accounts_empty(self) -> None:
        ids_before = [r[0] for r in self.conn.execute("SELECT id FROM items ORDER BY id")]
        db.init(self.conn)
        db.init(self.conn)  # a second start must change nothing

        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], 3)
        self.assertEqual(self.count("legacy_attempts"), 2)
        self.assertEqual(self.count("legacy_reviews"), 1)
        self.assertEqual(self.count("legacy_decisions"), 1)
        self.assertEqual(self.count("legacy_settings"), 1)
        self.assertEqual([r[0] for r in self.conn.execute("SELECT item_id FROM legacy_stars")], [40])
        for table in PER_USER:
            self.assertEqual(self.count(table), 0, table)
        self.assertEqual([r[0] for r in self.conn.execute("SELECT id FROM items ORDER BY id")], ids_before)
        self.assertIn("user_id", db._columns(self.conn, "attempts"))
        self.assertNotIn("starred", db._columns(self.conn, "items"))

    def test_seeding_a_migrated_database_keeps_ids_and_adds_the_sde_sheet(self) -> None:
        db.init(self.conn)
        db.seed(self.conn)
        db.seed(self.conn)
        scalar = lambda sql: self.conn.execute(sql).fetchone()[0]  # noqa: E731
        self.assertEqual(scalar("SELECT COUNT(*) FROM items WHERE track = 'sde'"), 153)
        self.assertEqual(self.count("legacy_attempts"), 2)
        self.assertEqual(scalar("SELECT COUNT(*) FROM items WHERE id IN (10, 20, 30, 40)"), 4, "old ids survive a reseed")

    def test_items_now_accept_the_sde_track(self) -> None:
        db.init(self.conn)
        self.conn.execute("INSERT INTO items (key, track, block, title, seq) VALUES ('sde:x', 'sde', '1', 'T', 1)")

    def test_foreign_keys_are_back_on_and_enforced(self) -> None:
        db.init(self.conn)
        self.assertEqual(self.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO attempts (user_id, item_id, on_date, mode) VALUES (999, 10, '2026-10-01', 'solve')"
            )

    def test_a_failed_migration_leaves_the_v2_file_intact(self) -> None:
        self.conn.execute("CREATE TABLE items_v3 (x)")  # makes the rebuild fail midway
        self.conn.commit()
        with self.assertRaises(sqlite3.OperationalError):
            db.init(self.conn)
        self.assertEqual(self.conn.execute("PRAGMA user_version").fetchone()[0], 2)
        self.assertEqual(self.count("attempts"), 2)
        self.assertEqual(self.count("legacy_attempts") if self._has("legacy_attempts") else 0, 0)
        self.assertEqual(self.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def _has(self, name: str) -> bool:
        return bool(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (name,)).fetchone())


class RealV2FileTest(unittest.TestCase):
    """A file written by the shipped v2 code, seeded with the real curriculum, then upgraded."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        db.DB_PATH = v2.DB_PATH = Path(self.tmp.name) / "prep.db"
        db.SEED_DIR = v2.SEED_DIR = SEED
        old = v2.connect()
        v2.init(old)
        v2.seed(old)
        dsa = [r["id"] for r in old.execute("SELECT id FROM items WHERE track = 'dsa' ORDER BY seq LIMIT 3")]
        a2z = old.execute("SELECT id FROM items WHERE track = 'a2z' ORDER BY seq LIMIT 1").fetchone()["id"]
        for item in dsa:
            old.execute("INSERT INTO attempts (item_id, on_date, mode, score) VALUES (?,?,?,?)", (item, "2026-10-01", "solve", 2))
            old.execute("INSERT INTO reviews (item_id, kind, due_date) VALUES (?,?,?)", (item, "recall", "2026-10-02"))
        old.execute("INSERT INTO decisions (item_id, chose, on_date) VALUES (?,?,?)", (dsa[0], "heap", "2026-10-01"))
        old.execute("UPDATE items SET starred = 1 WHERE id = ?", (a2z,))
        v2.set_setting(old, "started_on", "2026-10-01")
        self.keys = {r["id"]: r["key"] for r in old.execute("SELECT id, key FROM items")}
        self.starred, self.dsa = a2z, dsa
        self.old_settings = old.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        old.close()
        self.conn = db.connect()
        self.addCleanup(self.conn.close)

    def scalar(self, sql: str) -> int:
        return self.conn.execute(sql).fetchone()[0]

    def test_startup_on_a_live_v2_file_keeps_every_item_and_copies_progress(self) -> None:
        for _ in range(2):  # the container runs init and seed on every start
            db.init(self.conn)
            db.seed(self.conn)

        self.assertEqual(self.scalar("PRAGMA user_version"), 3)
        self.assertEqual({r["id"]: r["key"] for r in self.conn.execute("SELECT id, key FROM items") if r["id"] in self.keys}, self.keys)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM items"), len(self.keys) + 153)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM legacy_attempts"), 3)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM legacy_reviews"), 3)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM legacy_decisions"), 1)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM legacy_settings"), self.old_settings)
        self.assertEqual([r[0] for r in self.conn.execute("SELECT item_id FROM legacy_stars")], [self.starred])
        self.assertEqual(self.scalar("SELECT value FROM legacy_settings WHERE key = 'started_on'"), "2026-10-01")
        for table in PER_USER:
            self.assertEqual(self.scalar(f"SELECT COUNT(*) FROM {table}"), 0, table)

    def test_seeding_the_upgraded_file_reuses_the_existing_rows(self) -> None:
        db.init(self.conn)
        before = self.scalar("SELECT COUNT(*) FROM items WHERE track != 'sde'")
        db.seed(self.conn)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM items WHERE track != 'sde'"), before, "no duplicate a2z or plan rows")
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM items WHERE track = 'a2z'"), 495)


class SeedListsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "prep.db"
        db.SEED_DIR = SEED
        self.conn = db.connect()
        db.init(self.conn)
        db.seed(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.tmp.cleanup()

    def test_sde_sheet_is_seeded_and_reseeding_is_stable(self) -> None:
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items WHERE track = 'sde'").fetchone()[0], 153)
        before = self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        db.seed(self.conn)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0], before)

    def test_anchors_exist_for_sde_and_a2z_one_per_lecture(self) -> None:
        for track, groups in (("a2z", 84), ("sde", 27)):
            anchors = self.conn.execute(
                "SELECT COUNT(*) FROM items WHERE track = ? AND is_anchor = 1", (track,)
            ).fetchone()[0]
            self.assertEqual(anchors, groups, track)
            first = self.conn.execute(
                "SELECT is_anchor FROM items WHERE track = ? ORDER BY seq LIMIT 1", (track,)
            ).fetchone()[0]
            self.assertEqual(first, 1)

    def test_plan_keeps_one_anchor_per_numbered_block(self) -> None:
        blocks = self.conn.execute(
            "SELECT COUNT(DISTINCT block) FROM items WHERE track = 'dsa' AND block GLOB '[0-9]*'"
        ).fetchone()[0]
        anchors = self.conn.execute(
            "SELECT COUNT(*) FROM items WHERE track = 'dsa' AND block GLOB '[0-9]*' AND is_anchor = 1"
        ).fetchone()[0]
        self.assertEqual(anchors, blocks)

    def test_canonical_record_prefers_plan_then_sde_then_a2z(self) -> None:
        canon = lists.canonical_ids(self.conn)
        track_of = {r["id"]: r["track"] for r in self.conn.execute("SELECT id, track FROM items")}
        by_slug: dict[str, set[str]] = {}
        for r in self.conn.execute("SELECT slug, track FROM items WHERE slug IS NOT NULL AND track IN ('dsa','sde','a2z')"):
            by_slug.setdefault(r["slug"], set()).add(r["track"])
        for item_id, canonical in canon.items():
            tracks = by_slug[self.conn.execute("SELECT slug FROM items WHERE id = ?", (item_id,)).fetchone()[0]]
            expected = next(t for t in ("dsa", "sde", "a2z") if t in tracks)
            self.assertEqual(track_of[canonical], expected)
            self.assertEqual(lists.canonical_of(self.conn, item_id), canonical)
        self.assertTrue(any(canon[i] != i for i in canon), "the lists overlap, so some rows are not canonical")

    def test_list_totals_and_titles(self) -> None:
        public = {entry["key"]: entry for entry in lists.public_lists(self.conn)}
        self.assertEqual(public["sde"]["title"], "Striver SDE sheet (153)")
        self.assertEqual(public["a2z"]["title"], "Striver A2Z sheet (495)")
        self.assertTrue(public["plan"]["title"].startswith("Prep plan ("))


if __name__ == "__main__":
    unittest.main()
