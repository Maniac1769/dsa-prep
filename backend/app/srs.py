"""Spaced-review scheduling rules.

Pure functions. No database access, no clock access except what is passed in.
Every rule here is written down in DSA-SYSTEM.md or SYSTEM-DESIGN.md; if you change
one, change it there too.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

Track = Literal["dsa", "lld", "hld", "prep", "a2z", "sde"]
ReviewKind = Literal["recall", "full_solve", "rebuild"]
Outcome = Literal["pass", "fail"]


@dataclass(frozen=True)
class TrackConfig:
    """Intervals and queue caps for one track.

    recall_offsets: days after first study for short recall prompts.
    anchor_offsets: days after first study for a full re-solve (DSA) or rebuild (design).
    anchor_kind:    what the anchor review is called on this track.
    """

    recall_offsets: tuple[int, ...]
    anchor_offsets: tuple[int, ...]
    anchor_kind: ReviewKind
    max_queued_anchor: int
    max_overdue_recall: int
    retire_after_clean: int
    retire_min_gap_days: int


DSA = TrackConfig(
    recall_offsets=(1, 7, 21, 60),
    # +7 and +30 are full re-solves; the +60 touch stays a short recall or transfer,
    # per DSA-SYSTEM.md. Anchor offsets replace the recall at the same offset.
    anchor_offsets=(7, 30),
    anchor_kind="full_solve",
    max_queued_anchor=6,
    max_overdue_recall=12,
    retire_after_clean=2,
    retire_min_gap_days=14,
)

DESIGN = TrackConfig(
    recall_offsets=(1, 10, 30, 75),
    anchor_offsets=(21, 60),
    anchor_kind="rebuild",
    max_queued_anchor=4,
    max_overdue_recall=8,
    retire_after_clean=2,
    retire_min_gap_days=21,
)

# Days to wait before a repair review after a failed one.
REPAIR_RECALL_DAYS = 1
REPAIR_ANCHOR_DAYS = 3

# A failure left unrepaired for longer than this forces review over new work.
STALE_FAILURE_DAYS = 7


def config_for(track: Track) -> TrackConfig:
    # A Striver sheet problem is a DSA problem: same ladder, same caps.
    return DSA if track in ("dsa", "a2z", "sde") else DESIGN


def schedule_after_first_study(
    track: Track, is_anchor: bool, studied_on: date
) -> list[tuple[ReviewKind, date]]:
    """Reviews created the first time an item is studied.

    On the DSA track an anchor's ~+7 full solve replaces the +7 short recall, so that
    recall offset is dropped rather than scheduled alongside it.
    """
    cfg = config_for(track)
    out: list[tuple[ReviewKind, date]] = []

    anchor_days = set(cfg.anchor_offsets) if is_anchor else set()
    for offset in cfg.recall_offsets:
        if offset in anchor_days:
            continue
        out.append(("recall", studied_on + timedelta(days=offset)))

    for offset in sorted(anchor_days):
        out.append((cfg.anchor_kind, studied_on + timedelta(days=offset)))

    return sorted(out, key=lambda pair: pair[1])


def schedule_after_review(
    track: Track,
    kind: ReviewKind,
    outcome: Outcome,
    done_on: date,
    prior_clean_anchor_dates: list[date],
) -> list[tuple[ReviewKind, date]]:
    """Reviews created when one review is completed.

    A pass on an anchor may retire it: two clean anchor reviews at least
    retire_min_gap_days apart mean no further anchor review is scheduled.
    A fail always repairs, regardless of history.
    """
    cfg = config_for(track)

    if outcome == "fail":
        repair: list[tuple[ReviewKind, date]] = [
            ("recall", done_on + timedelta(days=REPAIR_RECALL_DAYS)),
            (cfg.anchor_kind, done_on + timedelta(days=REPAIR_ANCHOR_DAYS)),
        ]
        return repair

    if kind == "recall":
        # A passed recall does not generate new work; the original ladder continues.
        return []

    clean = sorted(prior_clean_anchor_dates + [done_on])
    if len(clean) >= cfg.retire_after_clean:
        gap = (clean[-1] - clean[-cfg.retire_after_clean]).days
        if gap >= cfg.retire_min_gap_days:
            return []

    next_offset = cfg.anchor_offsets[-1] - cfg.anchor_offsets[0]
    return [(cfg.anchor_kind, done_on + timedelta(days=max(next_offset, 21)))]


@dataclass(frozen=True)
class QueueVerdict:
    """What the Today view is allowed to offer."""

    allow_new_work: bool
    reason: str
    queued_anchor: int
    overdue_recall: int
    stale_failure_days: int


def assess_queue(
    track: Track,
    today: date,
    queued_anchor_due_dates: list[date],
    overdue_recall_count: int,
    oldest_unrepaired_failure: date | None,
) -> QueueVerdict:
    """Decide whether new work is permitted, per the queue caps in the plan.

    The caps exist so revision cannot quietly grow until it eats the hour. When new
    work is blocked the answer is always 'do the review instead', never 'do both'.
    """
    cfg = config_for(track)
    queued = len([d for d in queued_anchor_due_dates if d <= today])

    stale = 0
    if oldest_unrepaired_failure is not None:
        stale = (today - oldest_unrepaired_failure).days

    if stale > STALE_FAILURE_DAYS:
        return QueueVerdict(
            False,
            f"A failed review has been waiting {stale} days. Repair it before new work.",
            queued,
            overdue_recall_count,
            stale,
        )

    if queued > cfg.max_queued_anchor:
        return QueueVerdict(
            False,
            f"{queued} anchor reviews are due (cap {cfg.max_queued_anchor}). "
            "This session is a review session.",
            queued,
            overdue_recall_count,
            stale,
        )

    if overdue_recall_count > cfg.max_overdue_recall:
        return QueueVerdict(
            False,
            f"{overdue_recall_count} short recalls are overdue (cap "
            f"{cfg.max_overdue_recall}). Clear them, and take two new items in the "
            "next block instead of three.",
            queued,
            overdue_recall_count,
            stale,
        )

    return QueueVerdict(True, "", queued, overdue_recall_count, stale)


def recall_prompt(track: Track, title: str) -> str:
    """The question to answer from memory. Decisions, not definitions.

    `title` is accepted for callers that render the prompt standalone; the prompt
    itself does not repeat it, because every screen shows the title beside it.
    """
    if track in ("dsa", "a2z", "sde"):
        return (
            "State the idea, why it is correct, the time and space complexity, and one "
            "edge case that breaks a naive version."
        )
    if track == "lld":
        return "Name the classes, and the one extension this design makes cheap."
    if track == "hld":
        return "Name the bottleneck you designed around, and the number that proved it was a bottleneck."
    return "What did you conclude, and what are you doing differently?"
