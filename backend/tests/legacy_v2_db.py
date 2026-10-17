# Frozen copy of backend/app/db.py at 4014bd2 (schema v2), unchanged. The migration test uses it to
# build a database exactly as the live container wrote it.
"""SQLite schema, migrations, and seeding from the curriculum CSVs.

One file on disk, one writer. Progress (attempts, reviews, decisions, the star and
anchor flags) is never dropped or overwritten by seeding: curriculum rows are
upserted on a stable natural key, and only curriculum columns are refreshed.
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get("DSA_DB_PATH", "/data/dsa-prep.db"))
SEED_DIR = Path(os.environ.get("DSA_SEED_DIR", "/app/seed"))

SCHEMA_VERSION = 2

ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS {name} (
    id           INTEGER PRIMARY KEY,
    key          TEXT NOT NULL UNIQUE,
    track        TEXT NOT NULL CHECK (track IN ('dsa','lld','hld','prep','a2z')),
    block        TEXT NOT NULL,
    phase        TEXT,
    platform     TEXT,
    external_id  TEXT,
    title        TEXT NOT NULL,
    url          TEXT,
    focus        TEXT,
    note         TEXT,
    difficulty   TEXT,
    slug         TEXT,
    article_url  TEXT,
    video_url    TEXT,
    section      TEXT,
    subsection   TEXT,
    is_anchor    INTEGER NOT NULL DEFAULT 0,
    starred      INTEGER NOT NULL DEFAULT 0,
    seq          INTEGER NOT NULL,
    retired      INTEGER NOT NULL DEFAULT 0
)
"""

SCHEMA = (
    ITEMS_DDL.format(name="items")
    + """;
CREATE INDEX IF NOT EXISTS items_track_seq ON items(track, seq);
CREATE INDEX IF NOT EXISTS items_slug ON items(slug);

CREATE TABLE IF NOT EXISTS attempts (
    id          INTEGER PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    on_date     TEXT NOT NULL,
    mode        TEXT NOT NULL CHECK (mode IN
                  ('learn','solve','resolve','recall','rebuild','mock')),
    score       INTEGER CHECK (score BETWEEN 0 AND 3),
    independent INTEGER NOT NULL DEFAULT 0,
    minutes     INTEGER,
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS attempts_item ON attempts(item_id, on_date);
CREATE INDEX IF NOT EXISTS attempts_date ON attempts(on_date);

CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL CHECK (kind IN ('recall','full_solve','rebuild')),
    due_date    TEXT NOT NULL,
    done_date   TEXT,
    outcome     TEXT CHECK (outcome IN ('pass','fail')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS reviews_due ON reviews(done_date, due_date);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    chose       TEXT NOT NULL,
    rejected    TEXT,
    because     TEXT,
    on_date     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
)

DEFAULT_SETTINGS = {
    # Weekdays carrying a system design session after the DSA hour. 0 = Monday.
    "design_days": "1,3,5",
    "design_minutes": "30",
    "dsa_minutes": "60",
    "timezone": "Asia/Kolkata",
    # Set on the first logged attempt; drives "week N" on the Today screen.
    "started_on": "",
}

LEETCODE_SLUG = re.compile(r"leetcode\.com/problems/([^/?#]+)")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}


def _migrate_v1_items(conn: sqlite3.Connection) -> None:
    """Rebuild a v1 items table into the v2 shape, keeping every id.

    v1 had a CHECK constraint without 'a2z' and no natural key. SQLite cannot alter a
    CHECK, so the table is rebuilt: create the new shape, copy rows across with ids
    intact (attempts and reviews reference them), drop the old table, rename. Foreign
    keys are disabled for the swap and re-enabled after.
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("BEGIN")
    conn.execute(ITEMS_DDL.format(name="items_v2"))
    conn.execute(
        """
        INSERT INTO items_v2 (id, key, track, block, phase, platform, external_id,
                              title, url, focus, note, is_anchor, seq, retired)
        SELECT id,
               CASE WHEN track = 'dsa'
                    THEN 'dsa:' || COALESCE(platform, '') || ':' || COALESCE(external_id, title)
                    ELSE track || ':' || block END,
               track, block, phase, platform, external_id, title, url, focus, note,
               is_anchor, seq, retired
        FROM items
        """
    )
    conn.execute("DROP TABLE items")
    conn.execute("ALTER TABLE items_v2 RENAME TO items")
    # v1 picked one anchor per distinct block label, and the Codeforces rows each had
    # their own "After Week N" label, so seven optional problems became anchors.
    conn.execute(
        "UPDATE items SET is_anchor = 0 WHERE track = 'dsa' AND platform = 'Codeforces' "
        "AND NOT EXISTS (SELECT 1 FROM reviews r WHERE r.item_id = items.id)"
    )
    conn.execute("COMMIT")
    conn.execute("PRAGMA foreign_keys = ON")


def init(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    has_items = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'items'"
    ).fetchone()
    if version < 2 and has_items and "key" not in _columns(conn, "items"):
        _migrate_v1_items(conn)
    conn.executescript(SCHEMA)
    for key, value in DEFAULT_SETTINGS.items():
        conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


def get_setting(conn: sqlite3.Connection, key: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        raise KeyError(f"unknown setting: {key}")
    return row["value"]


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


# Curriculum columns refreshed on every seed. Progress columns (is_anchor, starred,
# retired) are set on first insert only, so a reseed never undoes a user's choice.
_CURRICULUM = (
    "track", "block", "phase", "platform", "external_id", "title", "url", "focus",
    "note", "difficulty", "slug", "article_url", "video_url", "section", "subsection",
    "seq",
)


def _upsert(conn: sqlite3.Connection, row: dict) -> int:
    cols = ("key", *_CURRICULUM, "is_anchor")
    values = [row.get(c) for c in cols]
    updates = ", ".join(f"{c} = excluded.{c}" for c in _CURRICULUM)
    cur = conn.execute(
        f"INSERT INTO items ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)}) "
        f"ON CONFLICT(key) DO UPDATE SET {updates}",
        values,
    )
    return cur.rowcount


def _read_csv(name: str) -> list[dict]:
    path = SEED_DIR / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if (r.get("Title") or r.get("title"))]


def _leetcode_meta() -> dict[str, dict]:
    path = SEED_DIR / "leetcode-meta.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {r["slug"]: r for r in csv.DictReader(handle)}


def _blank(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def seed(conn: sqlite3.Connection) -> dict[str, int]:
    """Upsert every curriculum row. Safe to run on every start."""
    counts = {"dsa": 0, "lld": 0, "hld": 0, "prep": 0, "a2z": 0}
    meta = _leetcode_meta()
    seq = 0

    for row in _read_csv("problem-tracker.csv"):
        seq += 1
        url = _blank(row.get("URL"))
        match = LEETCODE_SLUG.search(url or "")
        slug = match.group(1) if match else None
        platform = row.get("Platform") or ""
        raw_block = (row.get("Block_or_prerequisite") or "").strip()
        is_codeforces = platform == "Codeforces"
        counts["dsa"] += _upsert(
            conn,
            {
                "key": f"dsa:{platform}:{row.get('Problem_ID') or row['Title']}",
                "track": "dsa",
                # Codeforces rows carry "After Week N" as their block label. They are an
                # optional side track, so they share one block and the label is kept as
                # the prerequisite note instead.
                "block": "cf" if is_codeforces else raw_block,
                "platform": platform,
                "external_id": row.get("Problem_ID"),
                "title": row["Title"],
                "url": url,
                "focus": _blank(row.get("Learning_focus")),
                "note": f"Available {raw_block[0].lower()}{raw_block[1:]}" if is_codeforces and raw_block else None,
                "difficulty": meta.get(slug or "", {}).get("difficulty"),
                "slug": slug,
                "seq": seq,
                "is_anchor": 0,
            },
        )

    for row in _read_csv("system-design-tracker.csv"):
        # CSV row order IS the running order (L1-L9, H1-H8, L10-L18, H9-H16, X1-X4).
        # Sorting by block name would run all of LLD before any HLD.
        seq += 1
        track = (row.get("Track") or "prep").lower()
        if track not in counts:
            track = "prep"
        counts[track] += _upsert(
            conn,
            {
                "key": f"{track}:{row['Block']}",
                "track": track,
                "block": row["Block"],
                "phase": row.get("Phase"),
                "title": row["Title"],
                "focus": _blank(row.get("Artefact")),
                "note": _blank(row.get("Prereq_note")),
                "section": _blank(row.get("Shape")),
                "seq": seq,
                "is_anchor": 1 if (row.get("Anchor_yes_no") or "").lower().startswith("y") else 0,
            },
        )

    for row in _read_csv("striver-a2z.csv"):
        seq += 1
        practice = _blank(row.get("practice_url"))
        slug = _blank(row.get("leetcode_slug"))
        if not slug:
            match = LEETCODE_SLUG.search(practice or "")
            slug = match.group(1) if match else None
        # The sheet grades its own problems basic / core / pro. Keep that scale for every
        # row so the sheet reads consistently; plan problems keep LeetCode's labels.
        difficulty = (_blank(row.get("difficulty")) or "").capitalize() or None
        counts["a2z"] += _upsert(
            conn,
            {
                "key": f"a2z:{row.get('step_no')}:{row.get('lecture')}:{row['title']}",
                "track": "a2z",
                "block": str(row.get("seq") or seq),
                "phase": row.get("step_no"),
                "title": row["title"],
                "url": practice,
                "difficulty": difficulty,
                "slug": slug,
                "article_url": _blank(row.get("article_url")),
                "video_url": _blank(row.get("video_url")),
                "section": _blank(row.get("step")),
                "subsection": _blank(row.get("lecture")),
                "seq": seq,
                "is_anchor": 0,
            },
        )

    _link_plan_to_a2z(conn)
    _default_dsa_anchors(conn)
    conn.commit()
    return counts


def _link_plan_to_a2z(conn: sqlite3.Connection) -> None:
    """Give plan problems the takeuforward article and video when A2Z covers them."""
    conn.execute(
        """
        UPDATE items SET
          article_url = COALESCE(article_url, (
            SELECT a.article_url FROM items a
            WHERE a.track = 'a2z' AND a.slug = items.slug AND a.article_url IS NOT NULL
            ORDER BY a.seq LIMIT 1)),
          video_url = COALESCE(video_url, (
            SELECT a.video_url FROM items a
            WHERE a.track = 'a2z' AND a.slug = items.slug AND a.video_url IS NOT NULL
            ORDER BY a.seq LIMIT 1))
        WHERE track = 'dsa' AND slug IS NOT NULL
        """
    )


def _default_dsa_anchors(conn: sqlite3.Connection) -> None:
    """One anchor per numbered DSA block, the block's first problem, unless one is set.

    The source CSV leaves the anchor column blank on every row. Without an anchor a
    block gets short recalls only and never a full re-solve. Codeforces is excluded:
    it is optional practice, not a learning block.
    """
    blocks = [
        r["block"]
        for r in conn.execute(
            "SELECT block FROM items WHERE track = 'dsa' AND block GLOB '[0-9]*' "
            "GROUP BY block HAVING SUM(is_anchor) = 0"
        )
    ]
    for block in blocks:
        conn.execute(
            "UPDATE items SET is_anchor = 1 WHERE id = ("
            "  SELECT id FROM items WHERE track = 'dsa' AND block = ? "
            "  ORDER BY seq LIMIT 1)",
            (block,),
        )
