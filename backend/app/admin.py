"""Operator commands, run inside the container: `python -m app.admin <command> <username>`.

reset-password  set a random one-time password, print it once, sign the account out everywhere
delete-user     remove the account and every row it owns
"""

from __future__ import annotations

import argparse
import sys

from . import auth, db
from .errors import Invalid


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.admin", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("reset-password", "delete-user"):
        commands.add_parser(name).add_argument("username")
    args = parser.parse_args(argv)

    with db.scope() as conn:
        db.init(conn)
        try:
            if args.command == "reset-password":
                password = auth.admin_reset_password(conn, args.username)
                print(f"One-time password for {args.username}: {password}")
                print("Sign in with it, then change it under Account.")
            else:
                user = conn.execute(
                    "SELECT id, username FROM users WHERE username = ?", (args.username.strip().lower(),)
                ).fetchone()
                if user is None:
                    raise Invalid(f"No user named {args.username[:40]!r}.")
                auth.remove_user(conn, user["id"], user["username"])
                print(f"Deleted {user['username']} and all their data.")
        except Invalid as exc:
            print(str(exc), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
