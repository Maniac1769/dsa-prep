"""One-line `event key=value` log records for decisions worth auditing.

Values that are not plain tokens are JSON-quoted and truncated, so a username typed
into a login form cannot forge a second log line.
"""

from __future__ import annotations

import json
import re

_PLAIN = re.compile(r"[A-Za-z0-9_.:/+-]{0,64}")


def _clean(value: object) -> str:
    text = str(value)
    return text if _PLAIN.fullmatch(text) else json.dumps(text[:64])


def log(event: str, **fields: object) -> None:
    print(event + "".join(f" {k}={_clean(v)}" for k, v in fields.items()), flush=True)
