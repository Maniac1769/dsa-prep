"""The Stats screen: the preferred list's completion bar plus design, and the week's work."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from . import core, sessions

BAR_LABEL = {"dsa": "Prep plan", "sde": "Striver SDE sheet", "a2z": "Striver A2Z sheet"}


def stats(conn: sqlite3.Connection, user: dict) -> dict:
    uid = user["id"]
    on = core.today_in_tz(user)
    target = user["weekly_sessions"] * 60 + user["design_sessions"] * user["design_minutes"]

    heat_from = on - timedelta(weeks=52)
    days = {
        r["on_date"]: {"on": r["on_date"], "entries": r["n"], "minutes": r["mins"] or 0}
        for r in conn.execute(
            "SELECT on_date, COUNT(*) AS n, SUM(COALESCE(minutes, 0)) AS mins FROM attempts "
            "WHERE user_id = ? AND on_date >= ? GROUP BY on_date", (uid, heat_from.isoformat()))
    }

    monday = sessions.monday_of(on)
    weekly = []
    for i in range(11, -1, -1):
        start = monday - timedelta(weeks=i)
        week = [d for k, d in days.items() if start <= date.fromisoformat(k) < start + timedelta(days=7)]
        weekly.append({"start": start, "minutes": sum(d["minutes"] for d in week),
                       "entries": sum(d["entries"] for d in week), "days": len(week), "current": i == 0})

    counts = {r["d"]: r["n"] for r in conn.execute(
        "SELECT CASE WHEN due_date < ? THEN ? ELSE due_date END AS d, COUNT(*) AS n FROM reviews "
        "WHERE user_id = ? AND done_date IS NULL AND due_date <= ? GROUP BY d",
        (on.isoformat(), on.isoformat(), uid, (on + timedelta(days=13)).isoformat()))}
    upcoming = [{"on": on + timedelta(days=i), "count": counts.get((on + timedelta(days=i)).isoformat(), 0)}
                for i in range(14)]

    def progress(label: str, rows: list[dict]) -> dict:
        return {"label": label, "solid": sum(1 for r in rows if r["status"] in core.SOLID),
                "started": sum(1 for r in rows if r["status"] in ("started", "helped")), "total": len(rows)}

    rows = core.items_for(conn, uid, core.DSA_GROUP)
    design_rows = core.items_for(conn, uid, core.DESIGN_GROUP)
    track = core.preferred_track(user)
    # Only the preferred list is a completion goal; a second list would be a second
    # backlog, so it gets no bar.
    bars = [
        progress(BAR_LABEL[track], core.counted(rows, track)),
        progress("LLD", [r for r in design_rows if r["track"] == "lld"]),
        progress("HLD", [r for r in design_rows if r["track"] == "hld"]),
    ]

    indep = conn.execute(
        "SELECT COUNT(*) AS n, SUM(independent) AS k FROM attempts "
        "WHERE user_id = ? AND mode IN ('solve','resolve','rebuild','mock')", (uid,)
    ).fetchone()
    nxt = core.next_new_from(core.preferred_pool(rows, user))
    return {
        "on": on,
        "target": target,
        "kpi": {
            "unaided": bars[0]["solid"], "plan_total": bars[0]["total"], "streak": core.streak(conn, uid, on),
            "week_minutes": weekly[-1]["minutes"], "target": target,
            "week_days": weekly[-1]["days"], "week_entries": weekly[-1]["entries"],
            "sessions_week": len(sessions.full_session_dates(conn, uid, monday, on)),
            "sessions_target": user["weekly_sessions"],
            "due_7": conn.execute(
                "SELECT COUNT(*) FROM reviews WHERE user_id = ? AND done_date IS NULL AND due_date <= ?",
                (uid, (on + timedelta(days=6)).isoformat())).fetchone()[0],
            "indep_rate": round(100 * (indep["k"] or 0) / indep["n"]) if indep["n"] else None,
        },
        "days": sorted(days.values(), key=lambda d: d["on"], reverse=True),
        "weekly": weekly,
        "upcoming": upcoming,
        "bars": bars,
        "any_activity": bool(days),
        "next_item": core.row_dto(nxt) if nxt else None,
    }
