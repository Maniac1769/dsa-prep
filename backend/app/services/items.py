"""One problem's page and every write that changes a user's progress on it.

Logging, starring and decisions always act on the canonical item (lists.py): a problem
that sits in two lists has one history, whichever row it was logged from.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from .. import curriculum, lists, srs
from ..errors import Conflict, Invalid, NotFound
from ..log import log
from . import core


def item_detail(conn: sqlite3.Connection, user: dict, item_id: int) -> dict:
    uid = user["id"]
    item = core.item_by_id(conn, uid, item_id)
    record_id = item["log_id"]
    plan_twin = None
    if item["track"] in ("sde", "a2z") and item.get("slug"):
        twin = conn.execute("SELECT id, block FROM items WHERE track = 'dsa' AND slug = ?", (item["slug"],)).fetchone()
        plan_twin = dict(twin) if twin else None
    return {
        "item": core.row_dto(item, subsection=item.get("subsection"), best=item.get("best"), log_id=record_id,
                             links=curriculum.design_links(item["block"]) if item["track"] in core.DESIGN_GROUP else []),
        "topic": curriculum.BLOCK_TOPICS.get(item["block"]) if item["track"] == "dsa" else None,
        "attempts": [dict(r) for r in conn.execute(
            "SELECT id, on_date, mode, score, independent, minutes, note FROM attempts "
            "WHERE user_id = ? AND item_id = ? ORDER BY on_date DESC, id DESC", (uid, record_id))],
        "reviews": [dict(r) for r in conn.execute(
            "SELECT id, kind, due_date, done_date, outcome FROM reviews WHERE user_id = ? AND item_id = ? "
            "ORDER BY due_date", (uid, record_id))],
        "decisions": [dict(r) for r in conn.execute(
            "SELECT id, chose, rejected, because, on_date FROM decisions WHERE user_id = ? AND item_id = ? "
            "ORDER BY on_date DESC, id DESC", (uid, record_id))],
        "plan_twin": plan_twin,
        "prompt": srs.recall_prompt(item["track"], item["title"]),
    }


# --- the review ladder ----------------------------------------------------------------


def _in_preferred_list(conn: sqlite3.Connection, user: dict, item: dict) -> bool:
    if item["track"] in core.DESIGN_GROUP:
        return True
    track = core.preferred_track(user)
    return any(r["track"] == track for r in lists.record_rows(conn, item["id"]))


def _ladder_eligible(conn: sqlite3.Connection, user: dict, item: dict) -> bool:
    """Problems in the preferred list get the review ladder when first studied; problems
    from other lists only when starred. A second sheet is never a second revision load."""
    return bool(item["starred"]) or _in_preferred_list(conn, user, item)


def _is_anchor(conn: sqlite3.Connection, user: dict, item: dict) -> bool:
    """Anchors get full re-solves. Judged by the preferred list's own row when the problem
    is in it (plan: first of its block; sheets: first of its lecture), else by the item."""
    if item["track"] not in core.DSA_GROUP:
        return bool(item["is_anchor"])
    track = core.preferred_track(user)
    mine = [r for r in lists.record_rows(conn, item["id"]) if r["track"] == track]
    return any(r["is_anchor"] for r in mine) if mine else bool(item["is_anchor"])


def _lay_ladder(conn: sqlite3.Connection, user: dict, item: dict, on: date) -> None:
    anchor = bool(item["starred"]) or _is_anchor(conn, user, item)
    for kind, due in srs.schedule_after_first_study(item["track"], anchor, on):
        conn.execute(
            "INSERT INTO reviews (user_id, item_id, kind, due_date) VALUES (?,?,?,?)",
            (user["id"], item["id"], kind, due.isoformat()),
        )


# --- writes ---------------------------------------------------------------------------


def log_attempt(conn: sqlite3.Connection, user: dict, item_id: int, mode: str, score: int | None,
                minutes: int | None, note: str, independent: bool | None) -> dict:
    """Record one attempt. The first real study of a problem lays the review ladder down.

    A recall is a touch, not a study: it never lays the ladder and never counts as a
    session. Problems outside the preferred list stay out of the review queue unless
    starred.
    """
    if mode not in core.MODES:
        raise Invalid(f"unknown mode {mode!r}")
    if score is not None and not 0 <= score <= 3:
        raise Invalid("score must be between 0 and 3")
    if minutes is not None and not 1 <= minutes <= 600:
        raise Invalid("minutes must be between 1 and 600")
    unaided = independent if independent is not None else (score or 0) >= 2
    on = core.today_in_tz(user)
    item = core.item_by_id(conn, user["id"], item_id, canonical=True)
    studied = conn.execute(
        "SELECT 1 FROM attempts WHERE user_id = ? AND item_id = ? AND mode != 'recall' LIMIT 1",
        (user["id"], item["id"]),
    ).fetchone()
    conn.execute(
        "INSERT INTO attempts (user_id, item_id, on_date, mode, score, independent, minutes, note) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (user["id"], item["id"], on.isoformat(), mode, score, 1 if unaided else 0, minutes, (note or "").strip() or None),
    )
    if mode != "recall" and not studied and _ladder_eligible(conn, user, item):
        _lay_ladder(conn, user, item, on)
    if not user["started_on"]:
        core.set_started_on(conn, user, on.isoformat())
    conn.commit()
    updated = core.item_by_id(conn, user["id"], item["id"], canonical=True)
    return {"id": item["id"], "status": updated["status"], "label": core.STATUS_LABEL[updated["status"]],
            "best": updated["best"], "attempts": updated["attempts"]}


def complete_review(conn: sqlite3.Connection, user: dict, review_id: int, outcome: str, note: str) -> dict:
    if outcome not in ("pass", "fail"):
        raise Invalid("outcome must be pass or fail")
    uid = user["id"]
    on = core.today_in_tz(user)
    row = conn.execute(
        "SELECT r.*, i.track FROM reviews r JOIN items i ON i.id = r.item_id WHERE r.id = ? AND r.user_id = ?",
        (review_id, uid),
    ).fetchone()
    if row is None:
        raise NotFound(f"no review {review_id}")
    if row["done_date"] is not None:
        raise Conflict("review already completed")
    conn.execute("UPDATE reviews SET done_date = ?, outcome = ? WHERE id = ? AND user_id = ?",
                 (on.isoformat(), outcome, review_id, uid))
    conn.execute(
        "INSERT INTO attempts (user_id, item_id, on_date, mode, score, independent, note) VALUES (?,?,?,?,?,?,?)",
        (uid, row["item_id"], on.isoformat(), "recall" if row["kind"] == "recall" else "rebuild",
         3 if outcome == "pass" else 0, 1 if outcome == "pass" else 0, (note or "").strip() or None),
    )
    anchor_kind = srs.config_for(row["track"]).anchor_kind
    clean = [
        date.fromisoformat(r["done_date"])
        for r in conn.execute(
            "SELECT done_date FROM reviews WHERE user_id = ? AND item_id = ? AND kind = ? AND outcome = 'pass' "
            "AND done_date IS NOT NULL AND id != ?",
            (uid, row["item_id"], anchor_kind, review_id),
        )
    ]
    for kind, due in srs.schedule_after_review(row["track"], row["kind"], outcome, on, clean):
        conn.execute("INSERT INTO reviews (user_id, item_id, kind, due_date) VALUES (?,?,?,?)",
                     (uid, row["item_id"], kind, due.isoformat()))
    conn.commit()
    return {"id": review_id, "outcome": outcome, "item_id": row["item_id"]}


def toggle_star(conn: sqlite3.Connection, user: dict, item_id: int) -> dict:
    """Starring puts a problem from outside the preferred list on the review ladder.
    Unstarring drops its open reviews unless the preferred list still owns the problem."""
    uid = user["id"]
    on = core.today_in_tz(user)
    item = core.item_by_id(conn, uid, item_id, canonical=True)
    if item["track"] not in core.DSA_GROUP:
        raise Invalid("only problems from the lists can be starred")
    starred = 0 if item["starred"] else 1
    conn.execute(
        "INSERT INTO user_items (user_id, item_id, starred) VALUES (?,?,?) "
        "ON CONFLICT(user_id, item_id) DO UPDATE SET starred = excluded.starred",
        (uid, item["id"], starred),
    )
    open_reviews = conn.execute(
        "SELECT COUNT(*) FROM reviews WHERE user_id = ? AND item_id = ? AND done_date IS NULL", (uid, item["id"])
    ).fetchone()[0]
    if starred and item["attempts"] and not open_reviews:
        _lay_ladder(conn, user, {**item, "starred": 1}, on)
    if not starred and not _in_preferred_list(conn, user, item):
        conn.execute("DELETE FROM reviews WHERE user_id = ? AND item_id = ? AND done_date IS NULL", (uid, item["id"]))
    conn.commit()
    return {"id": item["id"], "starred": bool(starred)}


def add_decision(conn: sqlite3.Connection, user: dict, item_id: int, chose: str, rejected: str, because: str) -> dict:
    item = core.item_by_id(conn, user["id"], item_id, canonical=True)
    if not chose.strip():
        raise Invalid("a decision needs what you chose")
    cur = conn.execute(
        "INSERT INTO decisions (user_id, item_id, chose, rejected, because, on_date) VALUES (?,?,?,?,?,?)",
        (user["id"], item["id"], chose.strip(), rejected.strip() or None, because.strip() or None,
         core.today_in_tz(user).isoformat()),
    )
    conn.commit()
    return {"id": cur.lastrowid}


def spread_overdue(conn: sqlite3.Connection, user: dict, per_day: int = 3) -> dict:
    """Move every overdue open review onto the coming days, oldest first.

    A missed week leaves a pile that would otherwise all land on today. Each day from
    today takes reviews until it holds per_day, counting what is already due that day.
    Completed reviews and reviews due in the future keep their dates.
    """
    if per_day < 1:
        raise Invalid("per_day must be at least 1")
    uid = user["id"]
    on = core.today_in_tz(user)
    overdue = [
        r["id"]
        for r in conn.execute(
            "SELECT r.id FROM reviews r JOIN items i ON i.id = r.item_id "
            "WHERE r.user_id = ? AND r.done_date IS NULL AND r.due_date < ? ORDER BY r.due_date, i.seq, r.id",
            (uid, on.isoformat()),
        )
    ]
    booked = {
        r["due_date"]: r["n"]
        for r in conn.execute(
            "SELECT due_date, COUNT(*) AS n FROM reviews WHERE user_id = ? AND done_date IS NULL "
            "AND due_date >= ? GROUP BY due_date",
            (uid, on.isoformat()),
        )
    }
    day, last = on, on
    for review_id in overdue:
        while booked.get(day.isoformat(), 0) >= per_day:
            day += timedelta(days=1)
        conn.execute("UPDATE reviews SET due_date = ? WHERE id = ? AND user_id = ?", (day.isoformat(), review_id, uid))
        booked[day.isoformat()] = booked.get(day.isoformat(), 0) + 1
        last = day
    conn.commit()
    log("spread overdue", user_id=uid, moved=len(overdue), per_day=per_day, through=last.isoformat())
    return {"moved": len(overdue), "through": last.isoformat()}
