"""Request plumbing shared by every router: the CSRF guard and the signed-in user."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request, Response

from . import auth, db
from .errors import Unauthorized


def same_site_write(request: Request) -> None:
    """Reject writes that did not come from this app's own script.

    A session cookie is ambient: a browser attaches it to any request, including a form
    another site submits. A custom header cannot be set by a plain form and forces a
    CORS preflight from script, which this app never grants, so requiring it on every
    write closes that path for all endpoints, body or not.
    """
    if request.method == "POST" and request.headers.get("x-prep") != "1":
        raise HTTPException(403, "missing X-Prep header")


@dataclass(frozen=True)
class Principal:
    """The signed-in user as a plain dict, plus the session token that proved it."""

    user: dict
    token: str


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        auth.COOKIE_NAME, token, max_age=auth.SESSION_DAYS * 86400, httponly=True,
        samesite="lax", secure=auth.cookie_secure(), path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        auth.COOKIE_NAME, httponly=True, samesite="lax", secure=auth.cookie_secure(), path="/"
    )


def current_user(request: Request, response: Response) -> Principal:
    """The account behind the session cookie, or 401. Every non-auth /api route uses it."""
    token = request.cookies.get(auth.COOKIE_NAME, "")
    with db.scope() as conn:
        found = auth.resolve_session(conn, token)
    if found is None:
        raise Unauthorized("Sign in to continue.")
    row, refreshed = found
    if refreshed:
        set_session_cookie(response, token)
    return Principal(dict(row), token)
