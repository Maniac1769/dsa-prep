"""Reset and undo, per user.

A reset first writes the user's progress to one JSON row in reset_snapshots, so undo
restores that user and nobody else. Curriculum rows and account settings are never
touched; only attempts, reviews, decisions and stars.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from .. import lists
from ..errors import Conflict, Invalid
from ..log import log
from . import core, sessions

SCOPES = ("week", "plan", "sde", "a2z", "design", "item", "all")
# Columns saved per table. ids are not kept: a restored row gets a fresh id, because the
# old one may have been handed to another user's row in the meantime.
_COLUMNS = {
    "attempts": ("item_id", "on_date", "mode", "score", "independent", "minutes", "note", "created_at"),
    "reviews": ("item_id", "kind", "due_date", "done_date", "outcome", "created_at"),
    "decisions": ("item_id", "chose", "rejected", "because", "on_date"),
    "user_items": ("item_id", "starred"),
}


def _attempt_mark(conn: sqlite3.Connection, user_id: int) -> list[int]:
    """Changes whenever an attempt is added, so undo can tell nothing was logged since."""
    row = conn.execute(
        "SELECT COUNT(*) AS n, COALESCE(MAX(id), 0) AS m FROM attempts WHERE user_id = ?", (user_id,)
    ).fetchone()
    return [row["n"], row["m"]]


def _week_bounds(user: dict) -> tuple[str, str]:
    """This Monday as a local date, and local Monday 00:00 as a UTC timestamp.

    attempts.on_date is a local date; reviews.created_at is SQLite datetime('now'),
    which is UTC. Each filter has to use its own clock.
    """
    monday = sessions.monday_of(core.today_in_tz(user))
    midnight = datetime.combine(monday, time.min, ZoneInfo(user["timezone"]))
    return monday.isoformat(), midnight.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _scope_ids(conn: sqlite3.Connection, scope: str, item_id: int | None) -> list[int] | None:
    """Canonical ids of the problems a scope clears; None means every problem.

    A list scope clears the shared records its rows point at, so resetting the SDE sheet
    also clears a problem it shares with the plan: there is one history, not two.
    """
    if scope == "all":
        return None
    if scope == "item":
        return [item_id]
    if scope == "design":
        return [r["id"] for r in conn.execute(f"SELECT id FROM items WHERE track IN ({core.marks(core.DESIGN_GROUP)})", core.DESIGN_GROUP)]
    track = lists.LISTS[scope].track
    canonical = lists.canonical_ids(conn)
    return sorted({canonical.get(r["id"], r["id"]) for r in conn.execute("SELECT id FROM items WHERE track = ?", (track,))})


def _where(ids: list[int] | None) -> tuple[str, list]:
    if ids is None:
        return "1 = 1", []
    return "item_id IN (SELECT value FROM json_each(?))", [json.dumps(ids)]


def _scope_counts(conn: sqlite3.Connection, user: dict, scope: str, item_id: int | None = None) -> dict:
    uid = user["id"]
    if scope == "week":
        monday, cutoff = _week_bounds(user)
        attempts = conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE user_id = ? AND on_date >= ?", (uid, monday)
        ).fetchone()[0]
        reviews = conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE user_id = ? AND (created_at >= ? OR done_date >= ?)",
            (uid, cutoff, monday),
        ).fetchone()[0]
    else:
        where, params = _where(_scope_ids(conn, scope, item_id))
        attempts = conn.execute(f"SELECT COUNT(*) FROM attempts WHERE user_id = ? AND {where}", [uid, *params]).fetchone()[0]
        reviews = conn.execute(f"SELECT COUNT(*) FROM reviews WHERE user_id = ? AND {where}", [uid, *params]).fetchone()[0]
    return {"attempts": attempts, "reviews": reviews}


def _undo_state(conn: sqlite3.Connection, user: dict) -> dict | None:
    row = conn.execute(
        "SELECT scope, title, mark, created_at FROM reset_snapshots WHERE user_id = ?", (user["id"],)
    ).fetchone()
    if row is None or json.loads(row["mark"]) != _attempt_mark(conn, user["id"]):
        return None
    return {"scope": row["scope"], "at": row["created_at"], "title": row["title"]}


def reset_preview(conn: sqlite3.Connection, user: dict) -> dict:
    monday, _ = _week_bounds(user)
    scopes = {s: _scope_counts(conn, user, s) for s in SCOPES if s != "item"}
    return {"scopes": scopes, "week_of": monday, "undo": _undo_state(conn, user)}


def _capture(conn: sqlite3.Connection, user: dict) -> str:
    state = {"started_on": user["started_on"]}
    for table, columns in _COLUMNS.items():
        state[table] = [
            list(r) for r in conn.execute(
                f"SELECT {', '.join(columns)} FROM {table} WHERE user_id = ? ORDER BY "
                + ("item_id" if table == "user_items" else "id"),
                (user["id"],),
            )
        ]
    return json.dumps(state)


def reset(conn: sqlite3.Connection, user: dict, scope: str, item_id: int | None = None) -> dict:
    """Clear progress for one scope, after saving it so the reset can be undone.

    week:   attempts and decisions dated this week, reviews scheduled this week, and
            reviews completed this week are reopened. Earlier weeks are untouched.
    plan / sde / a2z / design / item: every attempt, review and decision for those
            problems; the list scopes also clear their stars.
    all:    every attempt, review, decision and star.
    """
    if scope not in SCOPES:
        raise Invalid(f"unknown reset scope {scope!r}")
    uid = user["id"]
    title = None
    if scope == "item":
        if item_id is None:
            raise Invalid("resetting a problem needs its id")
        item = core.item_by_id(conn, uid, item_id, canonical=True)
        item_id, title = item["id"], item["title"]
    counts = _scope_counts(conn, user, scope, item_id)
    payload = _capture(conn, user)

    if scope == "week":
        monday, cutoff = _week_bounds(user)
        conn.execute("DELETE FROM attempts WHERE user_id = ? AND on_date >= ?", (uid, monday))
        conn.execute("DELETE FROM decisions WHERE user_id = ? AND on_date >= ?", (uid, monday))
        conn.execute("DELETE FROM reviews WHERE user_id = ? AND created_at >= ?", (uid, cutoff))
        conn.execute(
            "UPDATE reviews SET done_date = NULL, outcome = NULL WHERE user_id = ? AND done_date >= ?", (uid, monday)
        )
    else:
        where, params = _where(_scope_ids(conn, scope, item_id))
        for table in ("attempts", "reviews", "decisions"):
            conn.execute(f"DELETE FROM {table} WHERE user_id = ? AND {where}", [uid, *params])
        if scope in ("plan", "sde", "a2z", "all"):
            conn.execute(f"UPDATE user_items SET starred = 0 WHERE user_id = ? AND {where}", [uid, *params])

    first = conn.execute("SELECT MIN(on_date) AS d FROM attempts WHERE user_id = ?", (uid,)).fetchone()["d"]
    core.set_started_on(conn, user, first or "")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO reset_snapshots (user_id, scope, title, mark, payload, created_at) VALUES (?,?,?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET scope = excluded.scope, title = excluded.title, "
        "mark = excluded.mark, payload = excluded.payload, created_at = excluded.created_at",
        (uid, scope, title, json.dumps(_attempt_mark(conn, uid)), payload, stamp),
    )
    conn.commit()
    log("reset", user_id=uid, scope=scope, item=item_id, attempts=counts["attempts"], reviews=counts["reviews"])
    return {"scope": scope, **counts, "snapshot": stamp}


def undo_reset(conn: sqlite3.Connection, user: dict) -> dict:
    """Put this user's progress back as it was just before their last reset.

    Only offered while nothing has been logged since; restoring would drop that work.
    """
    state = _undo_state(conn, user)
    if state is None:
        raise Conflict("nothing to undo: no recent reset, or something was logged after it")
    uid = user["id"]
    saved = json.loads(conn.execute("SELECT payload FROM reset_snapshots WHERE user_id = ?", (uid,)).fetchone()["payload"])
    for table, columns in _COLUMNS.items():
        conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (uid,))
        for values in saved[table]:
            conn.execute(
                f"INSERT INTO {table} (user_id, {', '.join(columns)}) VALUES (?{',?' * len(columns)})", (uid, *values)
            )
    core.set_started_on(conn, user, saved["started_on"])
    conn.execute("DELETE FROM reset_snapshots WHERE user_id = ?", (uid,))
    conn.commit()
    log("undo reset", user_id=uid, scope=state["scope"])
    return {"restored": state["scope"]}

