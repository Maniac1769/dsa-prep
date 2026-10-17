"""Typed errors the routes map to the contract's status codes.

Services raise these; main.py turns them into `{"detail": ...}` responses.
NotFound 404, Invalid 400, Conflict 409, Unauthorized 401, Forbidden 403, TooMany 429.
"""

from __future__ import annotations


class NotFound(Exception):
    pass


class Invalid(Exception):
    pass


class Conflict(Exception):
    pass


class Unauthorized(Exception):
    pass


class Forbidden(Exception):
    pass


class TooMany(Exception):
    def __init__(self, message: str, retry_after: int) -> None:
        super().__init__(message)
        self.retry_after = max(1, retry_after)
