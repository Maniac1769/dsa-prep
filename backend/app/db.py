"""SQLite schema, migrations, and seeding from the curriculum CSVs.

One file on disk, one writer. Progress (attempts, reviews, decisions, stars) belongs to a
user and is never dropped or overwritten by seeding: curriculum rows are upserted on a
stable natural key, and only curriculum columns are refreshed.
"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from . import lists

DB_PATH = Path(os.environ.get("DSA_DB_PATH", "/data/dsa-prep.db"))
SEED_DIR = Path(os.environ.get("DSA_SEED_DIR", "/app/seed"))

SCHEMA_VERSION = 3

# The single-user (v2) shape. Kept so a v1 or v2 file on disk can be brought forward:
# the v3 migration copies attempts, reviews, decisions and settings out of these tables.
ITEMS_V2_DDL = """
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

V2_SCHEMA = (
    ITEMS_V2_DDL.format(name="items")
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

# Curriculum items are shared by every user. Stars moved to user_items, so there is no
# `starred` column here. `sde` joins the track CHECK for the Striver SDE sheet.
ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS {name} (
    id           INTEGER PRIMARY KEY,
    key          TEXT NOT NULL UNIQUE,
    track        TEXT NOT NULL CHECK (track IN ('dsa','lld','hld','prep','a2z','sde')),
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
    seq          INTEGER NOT NULL,
    retired      INTEGER NOT NULL DEFAULT 0
)
"""

_ITEM_COLUMNS = (
    "id, key, track, block, phase, platform, external_id, title, url, focus, note, "
    "difficulty, slug, article_url, video_url, section, subsection, is_anchor, seq, retired"
)

ITEMS_INDEXES = """
CREATE INDEX IF NOT EXISTS items_track_seq ON items(track, seq);
CREATE INDEX IF NOT EXISTS items_slug ON items(slug)
"""

# Everything below items is per user. Indexes lead with user_id so one account's reads
# never scan another's rows.
USER_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash   TEXT NOT NULL,
    preferred_list  TEXT NOT NULL DEFAULT 'plan' CHECK (preferred_list IN ('plan','sde','a2z')),
    timezone        TEXT NOT NULL,
    weekly_sessions INTEGER NOT NULL DEFAULT 5 CHECK (weekly_sessions BETWEEN 3 AND 7),
    design_sessions INTEGER NOT NULL DEFAULT 3 CHECK (design_sessions BETWEEN 0 AND 7),
    design_minutes  INTEGER NOT NULL DEFAULT 30 CHECK (design_minutes IN (15,30,45,60)),
    started_on      TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash  TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS auth_sessions_user ON auth_sessions(user_id);

CREATE TABLE IF NOT EXISTS login_failures (
    id        INTEGER PRIMARY KEY,
    username      TEXT NOT NULL,
    at            REAL NOT NULL,
    locked_until  REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS login_failures_user ON login_failures(username, at);

CREATE TABLE IF NOT EXISTS user_items (
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id  INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    starred  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, item_id)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS reset_snapshots (
    user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    scope       TEXT NOT NULL,
    title       TEXT,
    mark        TEXT NOT NULL,
    payload     TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS attempts_user_item ON attempts(user_id, item_id, on_date);
CREATE INDEX IF NOT EXISTS attempts_user_date ON attempts(user_id, on_date);

CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL CHECK (kind IN ('recall','full_solve','rebuild')),
    due_date    TEXT NOT NULL,
    done_date   TEXT,
    outcome     TEXT CHECK (outcome IN ('pass','fail')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS reviews_user_due ON reviews(user_id, done_date, due_date);
CREATE INDEX IF NOT EXISTS reviews_user_item ON reviews(user_id, item_id);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    chose       TEXT NOT NULL,
    rejected    TEXT,
    because     TEXT,
    on_date     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS decisions_user_item ON decisions(user_id, item_id)
"""

SCHEMA = ITEMS_DDL.format(name="items") + ";\n" + ITEMS_INDEXES + ";\n" + USER_TABLES

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
    conn.execute(ITEMS_V2_DDL.format(name="items_v2"))
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


def _statements(script: str) -> list[str]:
    """Split a DDL script into statements. executescript would commit mid-migration."""
    return [part.strip() for part in script.split(";") if part.strip()]


def _migrate_v3(conn: sqlite3.Connection) -> None:
    """Bring a single-user (v2) database to the per-user shape (v3).

    Progress cannot be attributed to an account that did not exist, so the old
    attempts, reviews, decisions, settings and starred item ids are copied into
    legacy_* tables and every account starts fresh. Nothing is deleted. items is rebuilt
    with every id kept: the track CHECK gains 'sde' and starred moves to user_items.

    One transaction, gated on user_version by the caller: a crash rolls back to the v2
    file and the next start retries. Foreign keys are off for the table swap (the new
    attempts/reviews/decisions are created only after items is renamed into place).
    """
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("BEGIN IMMEDIATE")
        for table in ("attempts", "reviews", "decisions", "settings"):
            conn.execute(f"CREATE TABLE IF NOT EXISTS legacy_{table} AS SELECT * FROM {table}")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS legacy_stars AS "
            "SELECT id AS item_id FROM items WHERE starred = 1"
        )
        conn.execute(ITEMS_DDL.format(name="items_v3"))
        conn.execute(
            f"INSERT INTO items_v3 ({_ITEM_COLUMNS}) SELECT {_ITEM_COLUMNS} FROM items"
        )
        for table in ("attempts", "reviews", "decisions", "settings", "items"):
            conn.execute(f"DROP TABLE {table}")
        conn.execute("ALTER TABLE items_v3 RENAME TO items")
        for statement in _statements(ITEMS_INDEXES + ";" + USER_TABLES):
            conn.execute(statement)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.execute("COMMIT")
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def init(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    has_items = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'items'"
    ).fetchone()
    if has_items and version < SCHEMA_VERSION:
        if version < 2 and "key" not in _columns(conn, "items"):
            _migrate_v1_items(conn)
        # A v1 file may lack tables v2 added; the migration copies from all of them.
        conn.executescript(V2_SCHEMA)
        _migrate_v3(conn)
    conn.executescript(SCHEMA)
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()


@contextmanager
def write_txn(conn: sqlite3.Connection) -> Iterator[None]:
    """Hold the write lock for a check-then-write that must not interleave."""
    conn.commit()
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        conn.rollback()
        raise
    conn.commit()


@contextmanager
def scope() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


# Curriculum columns refreshed on every seed. is_anchor and retired are set on first
# insert only, so a reseed never undoes an edit made to them.
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
    counts = {"dsa": 0, "lld": 0, "hld": 0, "prep": 0, "a2z": 0, "sde": 0}
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

    for track, filename in (("a2z", "striver-a2z.csv"), ("sde", "striver-sde.csv")):
        for row in _read_csv(filename):
            seq += 1
            practice = _blank(row.get("practice_url"))
            slug = _blank(row.get("leetcode_slug"))
            if not slug:
                match = LEETCODE_SLUG.search(practice or "")
                slug = match.group(1) if match else None
            # The sheets grade their own problems basic / core / pro. Keep that scale for
            # every row so a sheet reads consistently; plan problems keep LeetCode's labels.
            difficulty = (_blank(row.get("difficulty")) or "").capitalize() or None
            counts[track] += _upsert(
                conn,
                {
                    "key": f"{track}:{row.get('step_no')}:{row.get('lecture')}:{row['title']}",
                    "track": track,
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

    _link_plan_to_sheets(conn)
    lists.set_default_anchors(conn)
    conn.commit()
    return counts


def _link_plan_to_sheets(conn: sqlite3.Connection) -> None:
    """Give plan problems the takeuforward article and video when a Striver sheet covers them."""
    conn.execute(
        """
        UPDATE items SET
          article_url = COALESCE(article_url, (
            SELECT a.article_url FROM items a
            WHERE a.track IN ('a2z', 'sde') AND a.slug = items.slug AND a.article_url IS NOT NULL
            ORDER BY a.seq LIMIT 1)),
          video_url = COALESCE(video_url, (
            SELECT a.video_url FROM items a
            WHERE a.track IN ('a2z', 'sde') AND a.slug = items.slug AND a.video_url IS NOT NULL
            ORDER BY a.seq LIMIT 1))
        WHERE track = 'dsa' AND slug IS NOT NULL
        """
    )
