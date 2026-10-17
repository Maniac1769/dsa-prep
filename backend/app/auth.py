"""Accounts, passwords, sessions and login throttling.

Passwords are hashed with the stdlib's scrypt, so there is no dependency to vet. Session
tokens are random and only their SHA-256 is stored: a copy of the database cannot be
replayed as a login. Every function takes the clock as `now` so lockout and expiry can
be tested without sleeping.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import os
import re
import secrets
import sqlite3
from collections import deque
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import db, lists
from .errors import Conflict, Forbidden, Invalid, TooMany, Unauthorized
from .log import log

COOKIE_NAME = "prep_session"
SESSION_DAYS = 30
REFRESH_BELOW_DAYS = 15

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
PASSWORD_MIN, PASSWORD_MAX = 10, 128
USERNAME = re.compile(r"[a-z0-9_-]{3,24}")

LOCK_FAILURES, LOCK_WINDOW, LOCK_SECONDS = 5, 15 * 60, 15 * 60
GLOBAL_ATTEMPTS, GLOBAL_WINDOW = 30, 60

USER_FIELDS = (
    "id", "username", "preferred_list", "timezone", "weekly_sessions", "design_sessions",
    "design_minutes", "created_at",
)


def max_users() -> int:
    raw = os.environ.get("MAX_USERS", "20")
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"MAX_USERS must be a whole number, got {raw!r}") from exc


def cookie_secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "1") != "0"


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def user_dto(user: sqlite3.Row | dict) -> dict:
    return {k: user[k] for k in USER_FIELDS}


# --- passwords ----------------------------------------------------------------------


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32, maxmem=256 * r * (n + p + 2)
    )


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return "$".join(("scrypt", str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P), _b64(salt), _b64(digest)))


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check against `scrypt$n$r$p$salt$hash`. Raises ValueError if the
    stored value is not in that format, so a corrupt row is a loud fault, not a quiet no."""
    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        raise ValueError("stored password hash is not in scrypt$n$r$p$salt$hash format")
    try:
        n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
        salt, expected = base64.b64decode(parts[4], validate=True), base64.b64decode(parts[5], validate=True)
    except ValueError as exc:
        raise ValueError("stored password hash has unreadable fields") from exc
    if n < 2 or n & (n - 1) or n > 2**20 or not 1 <= r <= 32 or not 1 <= p <= 16:
        raise ValueError("stored password hash has out-of-range scrypt parameters")
    return hmac.compare_digest(_scrypt(password, salt, n, r, p), expected)


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password(secrets.token_urlsafe(16))


def check_password_rules(password: str) -> None:
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        raise Invalid(f"Password must be {PASSWORD_MIN} to {PASSWORD_MAX} characters.")


def normalize_username(username: str) -> str:
    name = username.strip().lower()
    if not USERNAME.fullmatch(name):
        raise Invalid("Username must be 3 to 24 characters: letters, digits, underscore or hyphen.")
    return name


# Browsers report CLDR's zone names, and CLDR keeps some names the tz database has since
# renamed (Chrome says Asia/Calcutta). Slim Debian images ship no legacy aliases, so these
# are mapped to the current name before validation and stored that way.
LEGACY_ZONES = {
    "Africa/Asmera": "Africa/Asmara",
    "America/Buenos_Aires": "America/Argentina/Buenos_Aires",
    "America/Catamarca": "America/Argentina/Catamarca",
    "America/Coral_Harbour": "America/Atikokan",
    "America/Cordoba": "America/Argentina/Cordoba",
    "America/Godthab": "America/Nuuk",
    "America/Indianapolis": "America/Indiana/Indianapolis",
    "America/Jujuy": "America/Argentina/Jujuy",
    "America/Louisville": "America/Kentucky/Louisville",
    "America/Mendoza": "America/Argentina/Mendoza",
    "Asia/Calcutta": "Asia/Kolkata",
    "Asia/Katmandu": "Asia/Kathmandu",
    "Asia/Rangoon": "Asia/Yangon",
    "Asia/Saigon": "Asia/Ho_Chi_Minh",
    "Atlantic/Faeroe": "Atlantic/Faroe",
    "Europe/Kiev": "Europe/Kyiv",
    "Europe/Uzhgorod": "Europe/Kyiv",
    "Europe/Zaporozhye": "Europe/Kyiv",
    "Pacific/Enderbury": "Pacific/Kanton",
    "Pacific/Ponape": "Pacific/Pohnpei",
    "Pacific/Truk": "Pacific/Chuuk",
}


def check_timezone(name: str) -> str:
    """The canonical IANA name for `name`, or Invalid. Callers must store the return value."""
    canonical = LEGACY_ZONES.get(name, name)
    try:
        ZoneInfo(canonical)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise Invalid(f"Unknown timezone {name[:40]!r}. Use an IANA name such as Asia/Kolkata.") from exc
    return canonical


# --- throttling ---------------------------------------------------------------------

# One uvicorn worker (see the Dockerfile), so a process-wide window is the global limit.
_attempts: deque[float] = deque()


def reset_throttle() -> None:
    _attempts.clear()


def _global_gate(moment: datetime, what: str) -> None:
    """Admit one login or register attempt, or refuse when the last minute is full."""
    now = moment.timestamp()
    while _attempts and _attempts[0] <= now - GLOBAL_WINDOW:
        _attempts.popleft()
    if len(_attempts) >= GLOBAL_ATTEMPTS:
        wait = math.ceil(_attempts[0] + GLOBAL_WINDOW - now)
        log("throttled globally", what=what, retry_after=wait)
        raise TooMany("Too many attempts. Wait a minute and try again.", wait)
    _attempts.append(now)


def _failure_key(username: str) -> str:
    return username.strip().lower()[:64]


def _check_not_locked(conn: sqlite3.Connection, key: str, moment: datetime, what: str) -> None:
    now = moment.timestamp()
    conn.execute("DELETE FROM login_failures WHERE at < ? AND locked_until < ?", (now - LOCK_WINDOW, now))
    locked = conn.execute(
        "SELECT MAX(locked_until) AS until FROM login_failures WHERE username = ?", (key,)
    ).fetchone()["until"]
    if locked and locked > now:
        wait = math.ceil(locked - now)
        log("throttled", what=what, user=key, retry_after=wait)
        raise TooMany("Too many failed attempts. Try again later.", wait)


def _record_failure(conn: sqlite3.Connection, key: str, moment: datetime) -> None:
    now = moment.timestamp()
    recent = conn.execute(
        "SELECT COUNT(*) AS n FROM login_failures WHERE username = ? AND at > ?", (key, now - LOCK_WINDOW)
    ).fetchone()["n"]
    locked_until = now + LOCK_SECONDS if recent + 1 >= LOCK_FAILURES else 0
    conn.execute(
        "INSERT INTO login_failures (username, at, locked_until) VALUES (?,?,?)", (key, now, locked_until)
    )
    conn.commit()


def _clear_failures(conn: sqlite3.Connection, key: str) -> None:
    conn.execute("DELETE FROM login_failures WHERE username = ?", (key,))


def _password_ok(stored: str, password: str, user_id: int | None) -> bool:
    try:
        return verify_password(password, stored)
    except ValueError as exc:
        log("password hash unreadable", user_id=user_id, reason=exc)
        return False


# --- sessions -----------------------------------------------------------------------


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(conn: sqlite3.Connection, user_id: int, now: datetime | None = None) -> str:
    moment = _now(now)
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO auth_sessions (token_hash, user_id, created_at, expires_at) VALUES (?,?,?,?)",
        (_token_hash(token), user_id, _iso(moment), _iso(moment + timedelta(days=SESSION_DAYS))),
    )
    conn.commit()
    return token


def resolve_session(
    conn: sqlite3.Connection, token: str, now: datetime | None = None
) -> tuple[sqlite3.Row, bool] | None:
    """The user a token belongs to, and whether its expiry was just pushed out (so the
    cookie must be re-sent). None for unknown or expired tokens."""
    if not token or len(token) > 256:
        return None
    moment = _now(now)
    row = conn.execute(
        "SELECT u.*, s.expires_at AS expires_at FROM auth_sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = ?",
        (_token_hash(token),),
    ).fetchone()
    if row is None:
        return None
    expires = datetime.fromisoformat(row["expires_at"])
    if expires <= moment:
        conn.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (_token_hash(token),))
        conn.commit()
        return None
    refreshed = expires - moment < timedelta(days=REFRESH_BELOW_DAYS)
    if refreshed:
        conn.execute(
            "UPDATE auth_sessions SET expires_at = ? WHERE token_hash = ?",
            (_iso(moment + timedelta(days=SESSION_DAYS)), _token_hash(token)),
        )
        conn.commit()
    return row, refreshed


def end_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (_token_hash(token),))
    conn.commit()


# --- account lifecycle --------------------------------------------------------------


def register(
    conn: sqlite3.Connection, username: str, password: str, timezone_name: str,
    preferred_list: str = lists.DEFAULT_LIST, now: datetime | None = None,
) -> tuple[sqlite3.Row, str]:
    moment = _now(now)
    _global_gate(moment, "register")
    name = normalize_username(username)
    check_password_rules(password)
    timezone_name = check_timezone(timezone_name)
    if preferred_list not in lists.LIST_KEYS:
        raise Invalid(f"Unknown list {preferred_list!r}.")
    hashed = hash_password(password)
    cap = max_users()
    # The count and the insert share one write lock, so two sign-ups cannot both take the
    # last place.
    with db.write_txn(conn):
        taken = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if taken >= cap:
            log("signup refused: sign-ups full", users=taken, cap=cap)
            raise Forbidden(f"Sign-ups are full: {min(taken, cap)} of {cap} places taken.")
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, preferred_list, timezone, created_at) "
                "VALUES (?,?,?,?,?)",
                (name, hashed, preferred_list, timezone_name, _iso(moment)),
            )
        except sqlite3.IntegrityError as exc:
            raise Conflict("That username is taken.") from exc
    user = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    token = create_session(conn, user["id"], moment)
    log("registered", user_id=user["id"], users=taken + 1, cap=cap)
    return user, token


def login(
    conn: sqlite3.Connection, username: str, password: str, now: datetime | None = None
) -> tuple[sqlite3.Row, str]:
    moment = _now(now)
    _global_gate(moment, "login")
    key = _failure_key(username)
    _check_not_locked(conn, key, moment, "login")
    user = conn.execute("SELECT * FROM users WHERE username = ?", (key,)).fetchone()
    # Unknown names still pay for one scrypt, so response time does not reveal them.
    stored = user["password_hash"] if user else _dummy_hash()
    matches = _password_ok(stored, password, user["id"] if user else None)
    if user is None or not matches:
        _record_failure(conn, key, moment)
        log("login failed", user=key)
        # Wrong username and wrong password read the same, so names cannot be probed.
        raise Unauthorized("Wrong username or password.")
    _clear_failures(conn, key)
    token = create_session(conn, user["id"], moment)
    log("login ok", user_id=user["id"])
    return user, token


def confirm_password(
    conn: sqlite3.Connection, user: sqlite3.Row | dict, password: str, now: datetime | None = None
) -> None:
    """Re-check the signed-in user's password before a sensitive change. Wrong guesses
    count toward the same lockout as login, so a stolen session cannot grind them out."""
    moment = _now(now)
    key = user["username"]
    _check_not_locked(conn, key, moment, "confirm")
    stored = conn.execute("SELECT password_hash FROM users WHERE id = ?", (user["id"],)).fetchone()["password_hash"]
    if not _password_ok(stored, password, user["id"]):
        _record_failure(conn, key, moment)
        log("password check failed", user_id=user["id"])
        raise Forbidden("Wrong password.")
    _clear_failures(conn, key)


def change_password(
    conn: sqlite3.Connection, user: sqlite3.Row | dict, current: str, new: str,
    keep_token: str | None, now: datetime | None = None,
) -> None:
    confirm_password(conn, user, current, now)
    check_password_rules(new)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new), user["id"]))
    if keep_token is None:
        conn.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user["id"],))
    else:
        conn.execute(
            "DELETE FROM auth_sessions WHERE user_id = ? AND token_hash != ?",
            (user["id"], _token_hash(keep_token)),
        )
    conn.commit()
    log("password changed", user_id=user["id"])


def delete_account(
    conn: sqlite3.Connection, user: sqlite3.Row | dict, password: str, now: datetime | None = None
) -> None:
    confirm_password(conn, user, password, now)
    remove_user(conn, user["id"], user["username"])


def remove_user(conn: sqlite3.Connection, user_id: int, username: str) -> None:
    """Delete the account; foreign keys cascade its sessions, progress and snapshots."""
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.execute("DELETE FROM login_failures WHERE username = ?", (username,))
    conn.commit()
    log("account deleted", user_id=user_id)


def admin_reset_password(conn: sqlite3.Connection, username: str) -> str:
    """Set a random one-time password and sign the account out everywhere."""
    user = conn.execute("SELECT id, username FROM users WHERE username = ?", (_failure_key(username),)).fetchone()
    if user is None:
        raise Invalid(f"No user named {username[:40]!r}.")
    password = secrets.token_urlsafe(12)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(password), user["id"]))
    conn.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user["id"],))
    conn.execute("DELETE FROM login_failures WHERE username = ?", (user["username"],))
    conn.commit()
    log("password reset by admin", user_id=user["id"])
    return password


def user_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def status(conn: sqlite3.Connection) -> dict:
    users, cap = user_count(conn), max_users()
    return {
        "registration_open": users < cap, "users": users, "cap": cap,
        "lists": lists.public_lists(conn),
    }

