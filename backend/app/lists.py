"""The three problem lists, the canonical-record rule, and the anchor rule.

A problem can sit in several lists. Progress is stored once per problem, on the
canonical item: the one in `plan`, else `sde`, else `a2z` (lowest seq within that list),
matched by LeetCode slug. Rows in the other lists point at it, so logging, starring and
resetting never split one problem's history across two records.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class ListDef:
    key: str
    track: str
    name: str


# List key `plan` is stored as track `dsa`. Order here is the canonical-record priority.
LISTS: dict[str, ListDef] = {
    "plan": ListDef("plan", "dsa", "Prep plan"),
    "sde": ListDef("sde", "sde", "Striver SDE sheet"),
    "a2z": ListDef("a2z", "a2z", "Striver A2Z sheet"),
}
LIST_KEYS = tuple(LISTS)
DSA_TRACKS = tuple(d.track for d in LISTS.values())
DEFAULT_LIST = "plan"
_PRIORITY = {track: n for n, track in enumerate(DSA_TRACKS)}


def title(key: str, total: int) -> str:
    return f"{LISTS[key].name} ({total})"


def totals(conn: sqlite3.Connection) -> dict[str, int]:
    """Problems per list. Codeforces is optional practice, never part of the plan total."""
    out = {}
    for key, d in LISTS.items():
        extra = " AND block != 'cf'" if key == "plan" else ""
        out[key] = conn.execute(
            f"SELECT COUNT(*) FROM items WHERE track = ?{extra}", (d.track,)
        ).fetchone()[0]
    return out


def public_lists(conn: sqlite3.Connection) -> list[dict]:
    counts = totals(conn)
    return [{"key": k, "title": title(k, counts[k]), "total": counts[k]} for k in LIST_KEYS]


def canonical_ids(conn: sqlite3.Connection) -> dict[int, int]:
    """Map every list item with a slug to the id of its canonical item.

    Items without a slug are their own record and are absent from the map.
    """
    best: dict[str, tuple[tuple[int, int], int]] = {}
    rows = conn.execute(
        f"SELECT id, slug, track, seq FROM items WHERE slug IS NOT NULL AND track IN "
        f"({','.join('?' for _ in DSA_TRACKS)})",
        DSA_TRACKS,
    ).fetchall()
    for r in rows:
        rank = (_PRIORITY[r["track"]], r["seq"])
        if r["slug"] not in best or rank < best[r["slug"]][0]:
            best[r["slug"]] = (rank, r["id"])
    return {r["id"]: best[r["slug"]][1] for r in rows}


def canonical_of(conn: sqlite3.Connection, item_id: int) -> int | None:
    """Canonical item id for any item id, or None when the item does not exist."""
    row = conn.execute("SELECT slug, track FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return None
    if row["slug"] is None or row["track"] not in DSA_TRACKS:
        return item_id
    case = " ".join(f"WHEN '{t}' THEN {n}" for t, n in _PRIORITY.items())
    return conn.execute(
        f"SELECT id FROM items WHERE slug = ? AND track IN ({','.join('?' for _ in DSA_TRACKS)}) "
        f"ORDER BY CASE track {case} END, seq LIMIT 1",
        (row["slug"], *DSA_TRACKS),
    ).fetchone()["id"]


def record_rows(conn: sqlite3.Connection, canonical_id: int) -> list[sqlite3.Row]:
    """Every list item that shares the canonical item's problem, itself included."""
    item = conn.execute("SELECT slug FROM items WHERE id = ?", (canonical_id,)).fetchone()
    if item is None or item["slug"] is None:
        return conn.execute("SELECT * FROM items WHERE id = ?", (canonical_id,)).fetchall()
    return conn.execute(
        f"SELECT * FROM items WHERE slug = ? AND track IN ({','.join('?' for _ in DSA_TRACKS)})",
        (item["slug"], *DSA_TRACKS),
    ).fetchall()


def set_default_anchors(conn: sqlite3.Connection) -> None:
    """Give every group a full re-solve anchor, its first problem, unless one is set.

    plan:     the first problem of each numbered block (Codeforces is excluded: it is
              optional practice, not a learning block).
    sde, a2z: the first problem of each lecture (`subsection`). The SDE sheet has no
              lectures, so each of its steps counts as one.
    Without an anchor a group gets short recalls only and never a full re-solve.
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
            "  SELECT id FROM items WHERE track = 'dsa' AND block = ? ORDER BY seq LIMIT 1)",
            (block,),
        )
    for track in ("sde", "a2z"):
        groups = conn.execute(
            "SELECT phase, COALESCE(subsection, '') AS sub FROM items WHERE track = ? "
            "GROUP BY phase, COALESCE(subsection, '') HAVING SUM(is_anchor) = 0",
            (track,),
        ).fetchall()
        for g in groups:
            conn.execute(
                "UPDATE items SET is_anchor = 1 WHERE id = ("
                "  SELECT id FROM items WHERE track = ? AND phase IS ? "
                "  AND COALESCE(subsection, '') = ? ORDER BY seq LIMIT 1)",
                (track, g["phase"], g["sub"]),
            )
