"""Static curriculum metadata: block topics, groups, the day plan, topic resources.

Everything here is read from the plan documents in seed/ or written down from them.
Progress lives in the database; this module only describes the curriculum.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from . import db


@dataclass(frozen=True)
class Group:
    key: str
    title: str
    first: int
    last: int
    resource_topic: str


# Mirrors the curriculum map in DSA-SYSTEM.md. resource_topic keys match
# seed/topic-resources.csv.
DSA_GROUPS: tuple[Group, ...] = (
    Group("arrays", "Arrays, strings and hashing", 1, 3, "arrays_hashing"),
    Group("pointers", "Two pointers and sliding window", 4, 6, "two_pointers_window"),
    Group("stacks", "Stacks", 7, 8, "stacks"),
    Group("bsearch", "Binary search", 9, 10, "binary_search"),
    Group("lists", "Linked lists", 11, 12, "linked_lists"),
    Group("recursion", "Recursion", 13, 13, "recursion"),
    Group("backtracking", "Backtracking", 14, 16, "backtracking"),
    Group("trees", "Trees", 17, 21, "trees"),
    Group("heaps", "Heaps", 22, 22, "heaps"),
    Group("greedy", "Greedy and intervals", 23, 24, "greedy_intervals"),
    Group("graphs", "Graphs", 25, 30, "graphs"),
    Group("tries", "Tries", 31, 31, "tries"),
    Group("dp", "Dynamic programming", 32, 37, "dp"),
    Group("bits", "Bit manipulation", 38, 38, "bits"),
    Group("advanced", "Advanced and combined", 39, 42, "dp"),
)

DESIGN_PHASES = {
    "1": "LLD foundations",
    "2": "HLD vocabulary and the canonical five",
    "3": "LLD under pressure",
    "4": "HLD depth",
    "5": "Interview preparation",
}


def group_for_block(block: str) -> Group | None:
    if not block.isdigit():
        return None
    n = int(block)
    return next((g for g in DSA_GROUPS if g.first <= n <= g.last), None)


_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|")


def _parse_block_topics() -> dict[str, str]:
    """Read the "Learn first" column of the curriculum table in DSA-SYSTEM.md."""
    path = db.SEED_DIR / "DSA-SYSTEM.md"
    if not path.exists():
        return {}
    topics: dict[str, str] = {}
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## The curriculum"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table:
            match = _ROW.match(line)
            if match:
                topics[match.group(1)] = match.group(2).strip()
    return topics


BLOCK_TOPICS = _parse_block_topics()


@dataclass(frozen=True)
class Segment:
    minutes: int
    label: str


@dataclass(frozen=True)
class DayPlan:
    name: str
    headline: str
    segments: tuple[Segment, ...]
    guidance: str


# What each kind of session is for. The weekly sequence (sessions.py) picks the kind;
# the segments are the hour budget from DSA-SYSTEM.md, 60 minutes a session.
SESSION_PLANS: dict[str, DayPlan] = {
    "learn": DayPlan(
        "Learn",
        "Learn and solve",
        (Segment(10, "Recall what is due"), Segment(45, "Learn and solve new work"), Segment(5, "Log it")),
        "One new problem, or the one you left unfinished. A hard one can take two sessions: "
        "finish it, then rebuild an assisted solution from a blank editor.",
    ),
    "resolve": DayPlan(
        "Re-solve",
        "Re-solve day",
        (Segment(5, "Recall"), Segment(50, "Full re-solves from a blank editor"), Segment(5, "Log it")),
        "One difficult old problem, or two shorter ones. No new work.",
    ),
    "mixed": DayPlan(
        "Mixed",
        "Mixed practice",
        (Segment(45, "One unseen problem, topic hidden"), Segment(10, "Compare with a good solution"), Segment(5, "Log it")),
        "Weeks 1 and 2: re-solve this week's work instead. From week 3, pick an unseen problem from a topic you have studied.",
    ),
    "catchup": DayPlan(
        "Catch up",
        "Catch up and plan",
        (Segment(20, "Clear overdue recalls"), Segment(25, "Finish unfinished work"), Segment(15, "Plan next week")),
        "Never double tomorrow's load to make up for a missed day.",
    ),
}

DESIGN_SHAPES = (
    ("Learn", "Read or watch one thing, close it, write a half page from memory."),
    ("Build", "Write real code or a real diagram. Stop at 30 minutes mid-sentence; resume next time."),
    ("Defend", "Attack a design you built: three interviewer questions, answered in writing."),
)

SESSION_STEPS = (
    ("0 to 5", "Restate the problem, check constraints, write examples, describe brute force."),
    ("5 to 20", "Look for the improvement. Write the invariant, recurrence, or why a structure helps."),
    ("20 to 35", "Code and test. No progress for 10 minutes: take one small hint."),
    ("35 to 45", "Debug, explain correctness and complexity, or study the missing idea."),
)

SCORES = (
    (0, "No valid approach"),
    (1, "Needed a hint, explanation or the solution"),
    (2, "Unaided, but slow or shaky"),
    (3, "Unaided, and can justify it"),
)


@dataclass(frozen=True)
class Resource:
    topic: str
    rank: int
    name: str
    creator: str
    url: str
    format: str
    language: str
    why: str
    caveat: str


def _load_resources() -> dict[str, list[Resource]]:
    path = db.SEED_DIR / "topic-resources.csv"
    if not path.exists():
        return {}
    out: dict[str, list[Resource]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            if not r.get("topic") or not r.get("resource"):
                continue
            out.setdefault(r["topic"], []).append(
                Resource(
                    topic=r["topic"],
                    rank=int(r.get("rank") or 9),
                    name=r["resource"],
                    creator=r.get("creator") or "",
                    url=r.get("url") or "",
                    format=r.get("format") or "",
                    language=r.get("language") or "",
                    why=r.get("why") or "",
                    caveat=r.get("caveat") or "",
                )
            )
    for items in out.values():
        items.sort(key=lambda res: res.rank)
    return out


RESOURCES = _load_resources()


@dataclass(frozen=True)
class DesignLink:
    kind: str  # watch | read | practice
    title: str
    url: str
    source: str
    note: str


_LINK_ORDER = {"watch": 0, "read": 1, "practice": 2}


def _load_design_links() -> dict[str, list[DesignLink]]:
    """Verified watch / read / practice links per system design block."""
    path = db.SEED_DIR / "design-links.csv"
    if not path.exists():
        return {}
    out: dict[str, list[DesignLink]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            url = (r.get("url") or "").strip()
            if not r.get("block") or not url.startswith("https://"):
                continue
            kind = (r.get("kind") or "read").strip().lower()
            out.setdefault(r["block"].strip(), []).append(
                DesignLink(kind if kind in _LINK_ORDER else "read", (r.get("title") or url).strip(), url,
                           (r.get("source") or "").strip(), (r.get("note") or "").strip())
            )
    for links in out.values():
        links.sort(key=lambda link: _LINK_ORDER[link.kind])
    return out


DESIGN_LINKS = _load_design_links()


def design_links(block: str) -> list[dict]:
    from dataclasses import asdict
    return [asdict(link) for link in DESIGN_LINKS.get(block, [])]


def sheet_source(filename: str) -> dict[str, str] | None:
    path = db.SEED_DIR / filename
    if not path.exists():
        return None
    fetched = datetime.fromtimestamp(path.stat().st_mtime).date()
    return {"fetched": fetched.strftime("%-d %B %Y")}


def week_number(started_on: str, today: date) -> int | None:
    if not started_on:
        return None
    return (today - date.fromisoformat(started_on)).days // 7 + 1
