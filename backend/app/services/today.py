"""The Today screen: what this session is for, what is due, and the 10-minute fallback."""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, replace
from datetime import timedelta

from .. import curriculum
from . import core, sessions


def today(conn: sqlite3.Connection, user: dict) -> dict:
    uid = user["id"]
    on = core.today_in_tz(user)
    rows = core.items_for(conn, uid, core.DSA_GROUP)
    pool = core.preferred_pool(rows, user)
    week = sessions.week_state(conn, user, on)
    kind = week.kind

    verdict = core.queue_verdict(conn, uid, on, core.DSA_GROUP)
    blocking, revisit = core.unfinished_from(pool)
    new_item = core.next_new_from(pool)
    reviews = core.due_reviews(conn, uid, on, core.DSA_GROUP)

    focus, focus_is_blocking = None, False
    if kind == "learn":
        if blocking:
            focus, focus_is_blocking = blocking[0], True
        elif verdict.allow_new_work:
            focus = new_item

    day = curriculum.SESSION_PLANS[kind]
    if not verdict.allow_new_work and kind in ("learn", "mixed"):
        # The queue caps win: new work is blocked, so this session is a review session.
        day = replace(curriculum.SESSION_PLANS["resolve"], name="Review", headline="Review session",
                      guidance=verdict.reason)

    pulled_forward = None
    if kind == "resolve" and not any(r["kind"] == "full_solve" for r in reviews):
        row = conn.execute(
            "SELECT r.id, r.kind, r.due_date, i.id AS item_id, i.title, i.track, i.block, i.url "
            "FROM reviews r JOIN items i ON i.id = r.item_id "
            "WHERE r.user_id = ? AND r.done_date IS NULL AND r.kind = 'full_solve' "
            "ORDER BY r.due_date LIMIT 1",
            (uid,),
        ).fetchone()
        pulled_forward = dict(row) if row else None

    this_week = []
    if kind == "mixed":
        cutoff = (on - timedelta(days=6)).isoformat()
        this_week = [core.row_dto(r) for r in core.records(rows) if (r["last_on"] or "") >= cutoff and r["attempts"]]

    ctx_item = blocking[0] if blocking else new_item
    ctx = ctx_item or {}
    in_plan = ctx.get("track") == "dsa"
    current_block = ctx.get("block") if in_plan else ctx.get("phase")
    group = curriculum.group_for_block(current_block or "") if in_plan else None
    resources = curriculum.RESOURCES.get(group.resource_topic, []) if group else []

    design = None
    design_done = sessions.design_sessions_done(conn, uid, week.monday, on)
    if design_done < user["design_sessions"]:
        d_rows = core.items_for(conn, uid, core.DESIGN_GROUP)
        d_verdict = core.queue_verdict(conn, uid, on, core.DESIGN_GROUP)
        d_blocking, _ = core.unfinished_from(d_rows)
        d_new = core.next_new_from(d_rows) if d_verdict.allow_new_work else None
        d_focus = d_blocking[0] if d_blocking else d_new
        design = {
            "minutes": user["design_minutes"],
            "reviews": core.due_reviews(conn, uid, on, core.DESIGN_GROUP),
            "verdict": core.verdict_dto(d_verdict),
            "focus": core.row_dto(d_focus, links=curriculum.design_links(d_focus["block"])) if d_focus else None,
            "focus_is_blocking": bool(d_blocking),
            "sessions_done": design_done,
            "sessions_target": user["design_sessions"],
        }

    info = core.preferred_info(rows, user)
    track = core.preferred_track(user)
    return {
        "on": on,
        "weekday": on.weekday(),
        "list": info,
        "context": core.context_for(ctx_item, rows),
        "session": {
            "kind": kind,
            "number": week.number,
            "of": user["weekly_sessions"],
            "done_today": week.done_today,
            "week_done": week.week_done,
            "short_days": week.short_days,
        },
        "day": asdict(day),
        "short_day": short_day(conn, uid, on, rows),
        "quiet_days": sessions.quiet_days(conn, uid, on),
        "week": curriculum.week_number(user["started_on"], on),
        "current_block": current_block,
        "block_topic": curriculum.BLOCK_TOPICS.get(current_block or "") if in_plan else None,
        "group": core.group_dto(group),
        "resource": core.resource_dto(resources[0] if resources else None),
        "week_days": core.week_activity(conn, uid, on),
        "streak": core.streak(conn, uid, on),
        "best_streak": core.best_streak(conn, uid),
        "activity": core.activity(conn, uid, on, weeks=16),
        "split": core.difficulty_split(rows, track),
        "due_week": conn.execute(
            "SELECT COUNT(*) FROM reviews WHERE user_id = ? AND done_date IS NULL AND due_date <= ?",
            (uid, (on + timedelta(days=6)).isoformat()),
        ).fetchone()[0],
        "reviews": reviews,
        "verdict": core.verdict_dto(verdict),
        "focus": core.row_dto(focus) if focus else None,
        "focus_is_blocking": focus_is_blocking,
        "blocking": [core.row_dto(r) for r in blocking[:3]],
        "revisit_count": len(revisit),
        "pulled_forward": pulled_forward,
        "this_week": this_week,
        "design": design,
        "unaided": info["solid"],
        "total": info["total"],
    }


def short_day(conn: sqlite3.Connection, user_id: int, on, rows: list[dict]) -> dict:
    """The 10-minute day: up to two due recalls, else the problem studied most recently
    before today (recalling something solved minutes ago tests nothing)."""
    due = [r for r in core.due_reviews(conn, user_id, on, core.DSA_GROUP) if r["kind"] == "recall"][:2]
    recall_item = None
    if not due:
        last = conn.execute(
            "SELECT a.item_id FROM attempts a JOIN items i ON i.id = a.item_id "
            f"WHERE a.user_id = ? AND i.track IN ({core.marks(core.DSA_GROUP)}) AND a.on_date < ? "
            "ORDER BY a.on_date DESC, a.id DESC LIMIT 1",
            (user_id, *core.DSA_GROUP, on.isoformat()),
        ).fetchone()
        if last:
            row = next((r for r in rows if r["id"] == last["item_id"]), None)
            recall_item = core.row_dto(row) if row else None
    return {"reviews": due, "recall_item": recall_item}
