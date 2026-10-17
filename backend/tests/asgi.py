"""A tiny in-process HTTP client for the ASGI app, so routes are tested with the stdlib only."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from urllib.parse import urlsplit


@dataclass
class Reply:
    status: int
    headers: dict[str, str]
    set_cookies: list[str]
    body: bytes

    def json(self):
        return json.loads(self.body)

    def text(self) -> str:
        return self.body.decode()


@dataclass
class Client:
    app: object
    prep: bool = True
    cookies: dict[str, str] = field(default_factory=dict)

    def request(self, method: str, url: str, body: dict | None = None, *, prep: bool | None = None) -> Reply:
        parts = urlsplit(url)
        raw = json.dumps(body).encode() if body is not None else b""
        headers = [(b"host", b"test"), (b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode())]
        if self.prep if prep is None else prep:
            headers.append((b"x-prep", b"1"))
        if self.cookies:
            headers.append((b"cookie", "; ".join(f"{k}={v}" for k, v in self.cookies.items()).encode()))
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method,
            "path": parts.path, "raw_path": parts.path.encode(), "query_string": parts.query.encode(),
            "headers": headers, "client": ("127.0.0.1", 1234), "server": ("test", 80), "scheme": "http",
            "root_path": "",
        }
        reply = asyncio.run(self._run(scope, raw))
        for line in reply.set_cookies:
            jar = SimpleCookie(line)
            for name, morsel in jar.items():
                if morsel["max-age"] == "0" or not morsel.value:
                    self.cookies.pop(name, None)
                else:
                    self.cookies[name] = morsel.value
        return reply

    async def _run(self, scope: dict, raw: bytes) -> Reply:
        sent = False

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": raw, "more_body": False}
            return {"type": "http.disconnect"}

        out: dict = {"headers": [], "body": b""}

        async def send(message):
            if message["type"] == "http.response.start":
                out["status"], out["headers"] = message["status"], message["headers"]
            elif message["type"] == "http.response.body":
                out["body"] += message.get("body", b"")

        await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in out["headers"]}
        cookies = [v.decode() for k, v in out["headers"] if k.decode().lower() == "set-cookie"]
        return Reply(out["status"], headers, cookies, out["body"])

    def get(self, url: str) -> Reply:
        return self.request("GET", url)

    def post(self, url: str, body: dict | None = None, **kw) -> Reply:
        return self.request("POST", url, body if body is not None else {}, **kw)
