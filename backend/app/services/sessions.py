"""The weekly session model: how many sessions the week holds and what each is for.

A week is a budget, not a calendar. The kind of the next session is read from a fixed
sequence by how many full sessions are already done this week, so a lost day shifts
nothing: the sequence resumes where it stopped and nothing doubles up.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from . import core

SEQUENCES: dict[int, tuple[str, ...]] = {
    3: ("learn", "learn", "resolve"),
    4: ("learn", "learn", "learn", "resolve"),
    5: ("learn", "learn", "learn", "resolve", "mixed"),
    6: ("learn", "learn", "learn", "learn", "resolve", "mixed"),
    7: ("learn", "learn", "learn", "learn", "resolve", "mixed", "catchup"),
}
QUIET_AFTER_DAYS = 2


def sequence(weekly_sessions: int) -> tuple[str, ...]:
    return SEQUENCES[weekly_sessions]


def kind_at(weekly_sessions: int, index: int) -> str:
    """Kind of the session at a 0-based index; past the budget the week repeats learn."""
    seq = sequence(weekly_sessions)
    return seq[index] if index < len(seq) else "learn"


def monday_of(on: date) -> date:
    return on - timedelta(days=on.weekday())


@dataclass(frozen=True)
class WeekState:
    monday: date
    full_dates: tuple[str, ...]
    short_days: int
    done_today: bool
    number: int
    kind: str
    week_done: bool

    @property
    def full_count(self) -> int:
        return len(self.full_dates)


def full_session_dates(conn: sqlite3.Connection, user_id: int, first: date, last: date) -> list[str]:
    """Days with at least one learn, solve, resolve, rebuild or mock attempt on a DSA problem."""
    return [
        r["on_date"]
        for r in conn.execute(
            "SELECT DISTINCT a.on_date FROM attempts a JOIN items i ON i.id = a.item_id "
            f"WHERE a.user_id = ? AND a.on_date BETWEEN ? AND ? AND a.mode IN ({core.marks(core.FULL_MODES)}) "
            f"AND i.track IN ({core.marks(core.DSA_GROUP)}) ORDER BY a.on_date",
            (user_id, first.isoformat(), last.isoformat(), *core.FULL_MODES, *core.DSA_GROUP),
        )
    ]


def short_day_count(conn: sqlite3.Connection, user_id: int, first: date, last: date) -> int:
    """Days whose only attempts are recalls."""
    return conn.execute(
        "SELECT COUNT(*) FROM (SELECT on_date FROM attempts WHERE user_id = ? AND on_date BETWEEN ? AND ? "
        "GROUP BY on_date HAVING SUM(mode != 'recall') = 0)",
        (user_id, first.isoformat(), last.isoformat()),
    ).fetchone()[0]


def week_state(conn: sqlite3.Connection, user: dict, on: date) -> WeekState:
    monday = monday_of(on)
    full = tuple(full_session_dates(conn, user["id"], monday, on))
    done_today = on.isoformat() in full
    # A day that already has a full session keeps that day's kind; otherwise today is
    # the next one in the sequence.
    index = len(full) - 1 if done_today else len(full)
    return WeekState(
        monday=monday,
        full_dates=full,
        short_days=short_day_count(conn, user["id"], monday, on),
        done_today=done_today,
        number=index + 1,
        kind=kind_at(user["weekly_sessions"], index),
        week_done=len(full) >= user["weekly_sessions"],
    )


def design_sessions_done(conn: sqlite3.Connection, user_id: int, monday: date, on: date) -> int:
    """Days this week with an attempt on an LLD, HLD or prep item."""
    return conn.execute(
        "SELECT COUNT(DISTINCT a.on_date) FROM attempts a JOIN items i ON i.id = a.item_id "
        f"WHERE a.user_id = ? AND a.on_date BETWEEN ? AND ? AND i.track IN ({core.marks(core.DESIGN_GROUP)})",
        (user_id, monday.isoformat(), on.isoformat(), *core.DESIGN_GROUP),
    ).fetchone()[0]


def quiet_days(conn: sqlite3.Connection, user_id: int, on: date) -> int | None:
    """Days since the last session of any kind, once that is two or more.

    A short day counts as a session: showing up for ten minutes is the restart we offer.
    None before the first attempt, so a new account is never told it has been away.
    """
    last = conn.execute("SELECT MAX(on_date) AS d FROM attempts WHERE user_id = ?", (user_id,)).fetchone()["d"]
    if last is None:
        return None
    gap = (on - date.fromisoformat(last)).days
    return gap if gap >= QUIET_AFTER_DAYS else None
