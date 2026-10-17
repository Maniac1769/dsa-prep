"""The plain-text reminder for one user, built from the same data as their Today screen."""

from __future__ import annotations

import os
import sqlite3

from . import core, today as today_view


def digest(conn: sqlite3.Connection, user: dict) -> str:
    t = today_view.today(conn, user)
    session = t["session"]
    lines = [f"{t['on'].strftime('%A')}: {t['day']['headline'].lower()} (session {session['number']} of {session['of']})"]

    dsa = []
    if t["reviews"]:
        dsa.append(f"  {len(t['reviews'])} due: " + ", ".join(r["title"] for r in t["reviews"][:4]))
    if not t["verdict"]["allow_new_work"]:
        dsa.append(f"  {t['verdict']['reason']}")
    elif t["blocking"] and session["kind"] == "learn":
        dsa.append(f"  finish first: {t['blocking'][0]['title']}")
    elif t["focus"]:
        dsa.append(f"  next: {t['focus']['title']}")
    if dsa:
        lines += ["\nDSA", *dsa]

    design = t["design"]
    if design:
        body = []
        if design["reviews"]:
            body.append(f"  {len(design['reviews'])} due: " + ", ".join(r["title"] for r in design["reviews"][:4]))
        if not design["verdict"]["allow_new_work"]:
            body.append(f"  {design['verdict']['reason']}")
        elif design["focus"]:
            body.append(f"  {'finish first' if design['focus_is_blocking'] else 'next'}: {design['focus']['title']}")
        if body:
            lines += ["\nDesign", *body]

    if t["quiet_days"]:
        lines.append(f"\n{t['quiet_days']} quiet days. Ten minutes is enough to restart: two recalls, nothing else.")
    base = os.environ.get("PUBLIC_URL", "")
    if len(lines) > 1 and base:
        lines.append(f"\n{base}/")
    return "\n".join(lines)
