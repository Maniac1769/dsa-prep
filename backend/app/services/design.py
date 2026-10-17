"""The System design screen: LLD, HLD and interview-prep items by phase."""

from __future__ import annotations

import sqlite3

from .. import curriculum
from . import core


def design(conn: sqlite3.Connection, user: dict) -> dict:
    rows = core.items_for(conn, user["id"], core.DESIGN_GROUP)
    nxt = core.next_new_from(rows)
    phases: list[dict] = []
    for r in rows:
        if not phases or phases[-1]["no"] != r["phase"]:
            phases.append({"no": r["phase"], "title": curriculum.DESIGN_PHASES.get(r["phase"] or "", ""), "rows": []})
        phases[-1]["rows"].append(core.row_dto(r, links=curriculum.design_links(r["block"])))
    for p in phases:
        p["done"] = sum(1 for r in p["rows"] if r["status"] in core.SOLID)
    return {"phases": phases, "next_id": (nxt or {}).get("id")}
