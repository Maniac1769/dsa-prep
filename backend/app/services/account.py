"""Account settings and the list switcher."""

from __future__ import annotations

import sqlite3

from .. import auth, lists
from ..errors import Invalid
from ..log import log
from . import core

DESIGN_MINUTES = (15, 30, 45, 60)
SETTING_FIELDS = ("preferred_list", "timezone", "weekly_sessions", "design_sessions", "design_minutes")


def update_settings(conn: sqlite3.Connection, user: dict, changes: dict) -> dict:
    """Apply the given fields, leave the rest. Switching list never touches progress:
    progress is stored per problem, and the new list simply reads it."""
    unknown = set(changes) - set(SETTING_FIELDS)
    if unknown:
        raise Invalid(f"Unknown settings: {', '.join(sorted(unknown))}.")
    if "preferred_list" in changes and changes["preferred_list"] not in lists.LIST_KEYS:
        raise Invalid(f"Unknown list {changes['preferred_list']!r}.")
    if "timezone" in changes:
        changes["timezone"] = auth.check_timezone(changes["timezone"])
    if "weekly_sessions" in changes and not 3 <= changes["weekly_sessions"] <= 7:
        raise Invalid("Weekly sessions must be between 3 and 7.")
    if "design_sessions" in changes and not 0 <= changes["design_sessions"] <= 7:
        raise Invalid("Design sessions must be between 0 and 7.")
    if "design_minutes" in changes and changes["design_minutes"] not in DESIGN_MINUTES:
        raise Invalid("Design minutes must be 15, 30, 45 or 60.")
    for column, value in changes.items():
        conn.execute(f"UPDATE users SET {column} = ? WHERE id = ?", (value, user["id"]))
        user[column] = value
    conn.commit()
    log("settings changed", user_id=user["id"], fields=",".join(sorted(changes)))
    return auth.user_dto(user)


def account_lists(conn: sqlite3.Connection, user: dict) -> dict:
    return {"lists": core.list_infos(core.items_for(conn, user["id"], core.DSA_GROUP), user)}
