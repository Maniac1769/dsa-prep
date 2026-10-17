"""The Plan screen: the week as a session budget, the pace, and the roadmap of the preferred list."""

from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from dataclasses import asdict

from .. import curriculum, srs
from . import core, sessions


def plan(conn: sqlite3.Connection, user: dict) -> dict:
    on = core.today_in_tz(user)
    rows = core.items_for(conn, user["id"], core.DSA_GROUP)
    design_rows = core.items_for(conn, user["id"], core.DESIGN_GROUP)
    pool = core.preferred_pool(rows, user)
    track = core.preferred_track(user)
    nxt = core.next_new_from(pool)
    d_nxt = core.next_new_from(design_rows)
    week = sessions.week_state(conn, user, on)

    seq = sessions.sequence(user["weekly_sessions"])
    session_list = []
    for i, kind in enumerate(seq):
        day = curriculum.SESSION_PLANS[kind]
        session_list.append({
            "kind": kind, "label": day.headline, "minutes": sum(s.minutes for s in day.segments),
            "done": i < week.full_count, "next": i == week.full_count,
        })

    # One new problem per learn session; a hard one takes two, an easy one none.
    new_per_week = seq.count("learn")
    remaining = sum(1 for r in pool if r["attempts"] == 0 and r["block"] != "cf" and not r["retired"])
    pace = {"new_per_week": new_per_week, "weeks_left": math.ceil(remaining / new_per_week)}

    if track == "dsa":
        roadmap, current, units_left = _plan_roadmap(rows, nxt)
    else:
        roadmap, current, units_left = _sheet_roadmap(pool, nxt)

    d_phase = (d_nxt or {}).get("phase")
    design_road = []
    for no, title in curriculum.DESIGN_PHASES.items():
        phase_rows = [r for r in design_rows if r["phase"] == no]
        state = ("current" if no == d_phase else "done" if d_phase is None or int(no) < int(d_phase) else "upcoming")
        design_road.append({"no": no, "title": title, "state": state, "count": len(phase_rows),
                            "done": sum(1 for r in phase_rows if r["status"] in core.SOLID)})

    extra = [{"key": k, "resources": [asdict(x) for x in curriculum.RESOURCES[k]]}
             for k in ("cpp_stl", "problem_solving") if k in curriculum.RESOURCES]
    return {
        "on": on,
        "sessions": session_list,
        "weekly_sessions": user["weekly_sessions"],
        "design_sessions": user["design_sessions"],
        "design_minutes": user["design_minutes"],
        "pace": pace,
        "total_minutes": sum(s["minutes"] for s in session_list) + user["design_sessions"] * user["design_minutes"],
        "roadmap": roadmap,
        "design_road": design_road,
        "current_block": current,
        "blocks_left": units_left,
        "session_steps": [{"t": t, "text": x} for t, x in curriculum.SESSION_STEPS],
        "design_shapes": [{"name": n, "text": x} for n, x in curriculum.DESIGN_SHAPES],
        "scores": [{"n": n, "text": x} for n, x in curriculum.SCORES],
        "ladder": asdict(srs.DSA),
        "design_ladder": asdict(srs.DESIGN),
        "extra_topics": extra,
    }


def _plan_roadmap(rows: list[dict], nxt: dict | None) -> tuple[list[dict], int | None, int]:
    by_block: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["track"] == "dsa":
            by_block[r["block"]].append(r)
    current = int(nxt["block"]) if nxt and nxt["block"].isdigit() else 43
    roadmap = []
    for g in curriculum.DSA_GROUPS:
        group_rows = [r for n in range(g.first, g.last + 1) for r in by_block.get(str(n), [])]
        state = "done" if current > g.last else "current" if g.first <= current <= g.last else "upcoming"
        roadmap.append({"group": core.group_dto(g), "state": state, "rows": len(group_rows),
                        "done": sum(1 for r in group_rows if r["status"] in core.SOLID),
                        "resources": [asdict(x) for x in curriculum.RESOURCES.get(g.resource_topic, [])]})
    return roadmap, (current if current <= 42 else None), max(0, 42 - current + 1) + 4


def _sheet_roadmap(pool: list[dict], nxt: dict | None) -> tuple[list[dict], int | None, int]:
    steps: list[dict] = []
    for r in pool:
        if not steps or steps[-1]["no"] != r["phase"]:
            steps.append({"title": r["section"] or "Unsorted", "no": r["phase"], "total": 0, "done": 0})
        steps[-1]["total"] += 1
        steps[-1]["done"] += r["status"] in core.SOLID
    here = (nxt or {}).get("phase")
    for s in steps:
        s["state"] = "done" if s["done"] == s["total"] else "current" if s["no"] == here else "upcoming"
    open_steps = sum(1 for s in steps if s["state"] != "done")
    return steps, int(here) if here and here.isdigit() else None, open_steps
