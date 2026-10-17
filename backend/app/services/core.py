"""Shared queries and row shapes: a user's progress per problem, queues, and activity.

Progress is stored per problem on its canonical item (lists.py). `items_for` returns
every row of the requested tracks with the progress of the record the row points at, so
a problem listed in two sheets shows one status in both.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .. import curriculum, lists, srs
from ..errors import NotFound

DSA_GROUP = lists.DSA_TRACKS
DESIGN_GROUP = ("lld", "hld", "prep")
STATUS_LABEL = {
    "todo": "Not started",
    "started": "Started, no approach yet",
    "helped": "Solved with help",
    "unaided": "Unaided, still shaky",
    "solid": "Unaided and solid",
}
MODES = ("learn", "solve", "resolve", "recall", "rebuild", "mock")
# What counts as a full session of work. A recall is a short-day touch, never a session.
FULL_MODES = ("learn", "solve", "resolve", "rebuild", "mock")
SOLID = ("unaided", "solid")


def today_in_tz(user: dict) -> date:
    return datetime.now(ZoneInfo(user["timezone"])).date()


def marks(values: tuple | list) -> str:
    return ",".join("?" for _ in values)


# --- status and rows ----------------------------------------------------------------


def status_of(attempts: int, best: int | None) -> str:
    if not attempts:
        return "todo"
    if best is None or best == 0:
        return "started"
    return {1: "helped", 2: "unaided", 3: "solid"}[best]


def _progress(item: dict, attempts: int, best: int | None, last_on: str | None, starred: bool, record_id: int) -> dict:
    item.update(attempts=attempts, best=best, last_on=last_on, starred=1 if starred else 0, log_id=record_id)
    item["status"] = status_of(attempts, best)
    return item


def items_for(conn: sqlite3.Connection, user_id: int, tracks: tuple[str, ...]) -> list[dict]:
    """Every row of `tracks` in seq order, each carrying its problem's progress for this user."""
    progress = {
        r["item_id"]: r
        for r in conn.execute(
            "SELECT item_id, COUNT(*) AS attempts, MAX(score) AS best, MAX(on_date) AS last_on "
            "FROM attempts WHERE user_id = ? GROUP BY item_id",
            (user_id,),
        )
    }
    stars = {
        r["item_id"]
        for r in conn.execute("SELECT item_id FROM user_items WHERE user_id = ? AND starred = 1", (user_id,))
    }
    canonical = lists.canonical_ids(conn)
    out = []
    for row in conn.execute(f"SELECT * FROM items WHERE track IN ({marks(tracks)}) ORDER BY seq", tracks):
        record_id = canonical.get(row["id"], row["id"])
        p = progress.get(record_id)
        out.append(_progress(
            dict(row), p["attempts"] if p else 0, p["best"] if p else None, p["last_on"] if p else None,
            record_id in stars, record_id,
        ))
    return out


def item_by_id(conn: sqlite3.Connection, user_id: int, item_id: int, *, canonical: bool = False) -> dict:
    """One item with its problem's progress. `canonical=True` returns the canonical item
    itself (what logging, starring and resetting act on); otherwise the row asked for."""
    record_id = lists.canonical_of(conn, item_id)
    if record_id is None:
        raise NotFound(f"no item {item_id}")
    row = conn.execute("SELECT * FROM items WHERE id = ?", (record_id if canonical else item_id,)).fetchone()
    p = conn.execute(
        "SELECT COUNT(*) AS attempts, MAX(score) AS best, MAX(on_date) AS last_on "
        "FROM attempts WHERE user_id = ? AND item_id = ?",
        (user_id, record_id),
    ).fetchone()
    starred = conn.execute(
        "SELECT 1 FROM user_items WHERE user_id = ? AND item_id = ? AND starred = 1", (user_id, record_id)
    ).fetchone()
    return _progress(dict(row), p["attempts"], p["best"], p["last_on"], bool(starred), record_id)


ROW_FIELDS = (
    "id", "track", "block", "phase", "title", "platform", "external_id", "difficulty", "url", "slug",
    "article_url", "video_url", "is_anchor", "starred", "status", "attempts", "focus", "note", "section",
)


def row_dto(item: dict, **extra) -> dict:
    """The slice of an item a list row renders. Keeps the 495-row sheet payload small."""
    out = {k: item.get(k) for k in ROW_FIELDS}
    out["is_anchor"] = bool(out["is_anchor"])
    out["starred"] = bool(out["starred"])
    out.update(extra)
    return out


# --- the preferred list ---------------------------------------------------------------


def preferred_track(user: dict) -> str:
    return lists.LISTS[user["preferred_list"]].track


def preferred_pool(rows: list[dict], user: dict) -> list[dict]:
    """The preferred list's rows, one per problem: what Today and Plan are built from."""
    track = preferred_track(user)
    seen: set[int] = set()
    pool = []
    for r in rows:
        if r["track"] != track or r["log_id"] in seen:
            continue
        seen.add(r["log_id"])
        pool.append(r)
    return pool


def counted(rows: list[dict], track: str) -> list[dict]:
    """A list's rows as counted in its total (Codeforces is optional, outside the plan)."""
    return [r for r in rows if r["track"] == track and not (track == "dsa" and r["block"] == "cf")]


def list_infos(rows: list[dict], user: dict) -> list[dict]:
    out = []
    for key, d in lists.LISTS.items():
        mine = counted(rows, d.track)
        out.append({
            "key": key, "title": lists.title(key, len(mine)), "total": len(mine),
            "solid": sum(1 for r in mine if r["status"] in SOLID), "preferred": key == user["preferred_list"],
        })
    return out


def preferred_info(rows: list[dict], user: dict) -> dict:
    return next(i for i in list_infos(rows, user) if i["preferred"])


def next_new_from(rows: list[dict]) -> dict | None:
    # Codeforces is an optional side track; it is never "next".
    return next((r for r in rows if not r["retired"] and r["block"] != "cf" and r["attempts"] == 0), None)


def unfinished_from(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Blocking: started, no approach yet (unscored or 0). Revisit: solved with help (1).

    The plan allows moving on from an assisted attempt; the anchor re-solve ladder is
    what checks whether it stuck, so a 1 never stalls new work.
    """
    return ([r for r in rows if r["status"] == "started"], [r for r in rows if r["status"] == "helped"])


def records(rows: list[dict]) -> list[dict]:
    """One row per problem: drop the rows that merely point at another list's record."""
    return [r for r in rows if r["log_id"] == r["id"]]


def context_for(item: dict | None, rows: list[dict]) -> str:
    """Where in its list an item sits, e.g. "Block 2 of 42, arrays, strings and hashing"."""
    if item is None:
        return ""
    if item["track"] == "dsa":
        if not item["block"].isdigit():
            return "Codeforces practice (optional)"
        total = len({r["block"] for r in rows if r["track"] == "dsa" and r["block"].isdigit()})
        group = curriculum.group_for_block(item["block"])
        label = f", {group.title[:1].lower()}{group.title[1:]}" if group else ""
        return f"Block {item['block']} of {total}{label}"
    steps = len({r["phase"] for r in rows if r["track"] == item["track"]})
    lecture = f", lecture {item['subsection']}" if item.get("subsection") else ""
    return f"Step {item['phase']} of {steps}: {item['section']}{lecture}"


# --- queue queries --------------------------------------------------------------------


def due_reviews(conn: sqlite3.Connection, user_id: int, on: date, tracks: tuple[str, ...] | None = None) -> list[dict]:
    sql = (
        "SELECT r.id, r.kind, r.due_date, i.id AS item_id, i.title, i.track, i.block, "
        "       i.url, i.difficulty "
        "FROM reviews r JOIN items i ON i.id = r.item_id "
        "WHERE r.user_id = ? AND r.done_date IS NULL AND r.due_date <= ? "
    )
    params: list = [user_id, on.isoformat()]
    if tracks:
        sql += f"AND i.track IN ({marks(tracks)}) "
        params.extend(tracks)
    sql += "ORDER BY r.due_date, i.seq"
    rows = [dict(r) for r in conn.execute(sql, params)]
    for row in rows:
        row["prompt"] = srs.recall_prompt(row["track"], row["title"])
        row["days_late"] = (on - date.fromisoformat(row["due_date"])).days
    return rows


def queue_verdict(conn: sqlite3.Connection, user_id: int, on: date, tracks: tuple[str, ...]) -> srs.QueueVerdict:
    """Caps apply to the whole track group, never per sub-track (that would double them)."""
    m = marks(tracks)
    anchor_kind = srs.config_for(tracks[0]).anchor_kind
    anchors = [
        date.fromisoformat(r["due_date"])
        for r in conn.execute(
            "SELECT r.due_date FROM reviews r JOIN items i ON i.id = r.item_id "
            f"WHERE r.user_id = ? AND r.done_date IS NULL AND r.kind = ? AND i.track IN ({m})",
            (user_id, anchor_kind, *tracks),
        )
    ]
    overdue = conn.execute(
        "SELECT COUNT(*) AS n FROM reviews r JOIN items i ON i.id = r.item_id "
        f"WHERE r.user_id = ? AND r.done_date IS NULL AND r.kind = 'recall' AND i.track IN ({m}) "
        "AND r.due_date < ?",
        (user_id, *tracks, on.isoformat()),
    ).fetchone()["n"]
    stale = conn.execute(
        "SELECT MIN(r.done_date) AS d FROM reviews r JOIN items i ON i.id = r.item_id "
        f"WHERE r.user_id = ? AND r.outcome = 'fail' AND i.track IN ({m}) AND NOT EXISTS ("
        "  SELECT 1 FROM reviews r2 WHERE r2.user_id = r.user_id AND r2.item_id = r.item_id "
        "  AND r2.done_date > r.done_date AND r2.outcome = 'pass')",
        (user_id, *tracks),
    ).fetchone()["d"]
    return srs.assess_queue(tracks[0], on, anchors, overdue, date.fromisoformat(stale) if stale else None)


def verdict_dto(v: srs.QueueVerdict) -> dict:
    return {"allow_new_work": v.allow_new_work, "reason": v.reason}


def group_dto(g: curriculum.Group | None) -> dict | None:
    return asdict(g) if g else None


def resource_dto(r: curriculum.Resource | None) -> dict | None:
    return asdict(r) if r else None


# --- activity ---------------------------------------------------------------------------


def week_activity(conn: sqlite3.Connection, user_id: int, on: date) -> list[dict]:
    monday = on - timedelta(days=on.weekday())
    worked = {
        r["on_date"]: r["mins"]
        for r in conn.execute(
            "SELECT on_date, SUM(COALESCE(minutes, 0)) AS mins FROM attempts "
            "WHERE user_id = ? AND on_date BETWEEN ? AND ? GROUP BY on_date",
            (user_id, monday.isoformat(), (monday + timedelta(days=6)).isoformat()),
        )
    }
    return [
        {"letter": d.strftime("%a")[0], "name": d.strftime("%A"), "worked": d.isoformat() in worked,
         "minutes": worked.get(d.isoformat(), 0), "today": d == on, "future": d > on}
        for d in (monday + timedelta(days=i) for i in range(7))
    ]


def _active_days(conn: sqlite3.Connection, user_id: int) -> set[str]:
    return {r["on_date"] for r in conn.execute("SELECT DISTINCT on_date FROM attempts WHERE user_id = ?", (user_id,))}


def streak(conn: sqlite3.Connection, user_id: int, on: date) -> int:
    active = _active_days(conn, user_id)
    # An unlogged today does not break a streak that ran through yesterday.
    cursor = on if on.isoformat() in active else on - timedelta(days=1)
    count = 0
    while cursor.isoformat() in active:
        count += 1
        cursor -= timedelta(days=1)
    return count


def longest_run(days: set[date]) -> int:
    best = 0
    for d in days:
        if d - timedelta(days=1) in days:
            continue
        n = 1
        while d + timedelta(days=n) in days:
            n += 1
        best = max(best, n)
    return best


def best_streak(conn: sqlite3.Connection, user_id: int) -> int:
    return longest_run({date.fromisoformat(d) for d in _active_days(conn, user_id)})


def activity(conn: sqlite3.Connection, user_id: int, on: date, weeks: int) -> dict:
    """Entries per day for the last `weeks` weeks, Monday-aligned, oldest first."""
    start = on - timedelta(days=on.weekday(), weeks=weeks - 1)
    counts = {
        r["on_date"]: r["n"]
        for r in conn.execute(
            "SELECT on_date, COUNT(*) AS n FROM attempts WHERE user_id = ? AND on_date >= ? GROUP BY on_date",
            (user_id, start.isoformat()),
        )
    }
    days = [start + timedelta(days=i) for i in range(weeks * 7)]
    return {
        "start": start,
        "days": [{"on": d, "n": counts.get(d.isoformat(), 0), "future": d > on} for d in days],
        "active_days": sum(1 for d in days if counts.get(d.isoformat())),
    }


def difficulty_split(rows: list[dict], track: str) -> list[dict]:
    """Unaided versus total per difficulty. Plan problems use LeetCode's labels, the
    Striver sheets their own basic / core / pro."""
    labels = ("Easy", "Medium", "Hard") if track == "dsa" else ("Basic", "Core", "Pro")
    mine = counted(rows, track)
    return [
        {"label": label,
         "solid": sum(1 for r in mine if (r["difficulty"] or "").lower() == label.lower() and r["status"] in SOLID),
         "total": sum(1 for r in mine if (r["difficulty"] or "").lower() == label.lower())}
        for label in labels
    ]


def set_started_on(conn: sqlite3.Connection, user: dict, value: str) -> None:
    conn.execute("UPDATE users SET started_on = ? WHERE id = ?", (value, user["id"]))
    user["started_on"] = value
