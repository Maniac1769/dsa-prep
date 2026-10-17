"""The Problems screen: the plan by block, or a Striver sheet by step and lecture."""

from __future__ import annotations

import sqlite3
from collections import defaultdict

from .. import curriculum, lists
from ..errors import Invalid
from . import core


def _block_state(rows: list[dict]) -> str:
    if rows and all(r["status"] in core.SOLID for r in rows):
        return "done"
    if any(r["status"] != "todo" for r in rows):
        return "partial"
    return "todo"


def problems(conn: sqlite3.Connection, user: dict, view: str) -> dict:
    if view not in lists.LIST_KEYS:
        raise Invalid(f"unknown view {view!r}")
    rows = core.items_for(conn, user["id"], core.DSA_GROUP)
    out = plan_problems(rows) if view == "plan" else sheet_problems(rows, view)
    out["lists"] = core.list_infos(rows, user)
    return out


def plan_problems(all_rows: list[dict]) -> dict:
    plan_rows = [r for r in all_rows if r["track"] == "dsa"]
    nxt = core.next_new_from(plan_rows)
    blocking, _ = core.unfinished_from(plan_rows)
    current = (blocking[0] if blocking else nxt or {}).get("block")
    by_block: dict[str, list[dict]] = defaultdict(list)
    for r in plan_rows:
        by_block[r["block"]].append(r)

    groups = []
    for g in curriculum.DSA_GROUPS:
        blocks = []
        for n in range(g.first, g.last + 1):
            rows = by_block.get(str(n), [])
            blocks.append({
                "block": str(n),
                "topic": curriculum.BLOCK_TOPICS.get(str(n), ""),
                "rows": [core.row_dto(r) for r in rows],
                "state": _block_state(rows),
                "done": sum(1 for r in rows if r["status"] in core.SOLID),
            })
        res = curriculum.RESOURCES.get(g.resource_topic, [])
        groups.append({
            "group": core.group_dto(g),
            "blocks": blocks,
            "resource": core.resource_dto(res[0] if res else None),
            "done": sum(b["done"] for b in blocks),
            "total": sum(len(b["rows"]) for b in blocks),
        })
    counted = core.counted(plan_rows, "dsa")
    return {
        "current_block": current,
        "groups": groups,
        "codeforces": [core.row_dto(r) for r in by_block.get("cf", [])],
        "solid": sum(1 for r in counted if r["status"] in core.SOLID),
        "total": len(counted),
        "a2z_total": sum(1 for r in all_rows if r["track"] == "a2z"),
    }


def sheet_problems(all_rows: list[dict], key: str) -> dict:
    """A Striver sheet: steps of lectures of rows. A row shared with another list shows
    that record's status and carries `log_id`, the item that logging acts on."""
    track = lists.LISTS[key].track
    block_of = {r["id"]: r["block"] for r in all_rows if r["track"] == "dsa"}
    steps: list[dict] = []
    overlap = 0
    for r in (r for r in all_rows if r["track"] == track):
        shared = r["log_id"] != r["id"]
        overlap += shared
        row = core.row_dto(r, plan_block=block_of.get(r["log_id"]), log_id=r["log_id"])
        if not steps or steps[-1]["title"] != (r["section"] or "Unsorted"):
            steps.append({"title": r["section"] or "Unsorted", "no": r["phase"], "lectures": []})
        lectures = steps[-1]["lectures"]
        # The SDE sheet has no lectures: each step is one, with an empty title.
        title = r["subsection"] or ""
        if not lectures or lectures[-1]["title"] != title:
            lectures.append({"title": title, "rows": []})
        lectures[-1]["rows"].append(row)
    for s in steps:
        rows = [r for lec in s["lectures"] for r in lec["rows"]]
        s["total"] = len(rows)
        s["done"] = sum(1 for r in rows if r["status"] in core.SOLID)
    return {
        "steps": steps,
        "total": sum(s["total"] for s in steps),
        "overlap": overlap,
        "source": curriculum.sheet_source(f"striver-{key}.csv"),
    }
