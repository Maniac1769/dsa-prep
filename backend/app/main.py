"""DSA and system design tracker: JSON API plus the built single-page app.

The backend owns every rule (accounts, scheduling, queue caps, seeding, migrations) and
returns exactly what each screen needs in one request. The front end (frontend/, TanStack
Router + Query) is built ahead of time and served as static files, so the runtime is still
one small Python process.

Sign-in is a session cookie. Writes also require an X-Prep header and JSON bodies: a
cookie is attached by the browser to any request, including a form another site submits,
and a custom header is something such a form cannot send.
"""

from __future__ import annotations

import hmac
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

from . import db, errors
from .deps import same_site_write
from .routers import account, auth, practice
from .services import digest as digest_view

BASE = Path(__file__).parent
DIST = Path(os.environ.get("DSA_WEB_DIST", BASE.parent.parent / "frontend" / "dist"))

STATUS = {
    errors.NotFound: 404,
    errors.Invalid: 400,
    errors.Conflict: 409,
    errors.Unauthorized: 401,
    errors.Forbidden: 403,
    errors.TooMany: 429,
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    with db.scope() as conn:
        db.init(conn)
        counts = db.seed(conn)
    print(f"seeded: {counts}", flush=True)
    yield


def _error_response(_: Request, exc: Exception) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)} if isinstance(exc, errors.TooMany) else None
    return JSONResponse({"detail": str(exc)}, status_code=STATUS[type(exc)], headers=headers)


def _validation_response(_: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    where = ".".join(str(part) for part in first["loc"] if part != "body")
    return JSONResponse({"detail": f"Invalid input{f' ({where})' if where else ''}: {first['msg']}."}, status_code=400)


class CacheHeaders(BaseHTTPMiddleware):
    """Hashed build assets never change, so cache them for a year. The HTML shell must
    always be revalidated, or a deploy would stay invisible until the cache expired."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        elif path.startswith("/assets/") and response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path.startswith("/fonts/") or path.endswith(".svg"):
            response.headers["Cache-Control"] = "public, max-age=604800"
        elif response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-cache"
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="Prep", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    for exc_type in STATUS:
        app.add_exception_handler(exc_type, _error_response)
    app.add_exception_handler(RequestValidationError, _validation_response)

    # The X-Prep guard is a router-level dependency, so it runs before any route's own
    # (including the session check): a forged write is refused 403 whether or not it is signed in.
    api = APIRouter(prefix="/api", dependencies=[Depends(same_site_write)])
    api.include_router(auth.router)
    api.include_router(account.router)
    api.include_router(practice.router)
    app.include_router(api)

    @app.get("/digest", response_class=PlainTextResponse)
    def digest(token: str = "", user: str = ""):
        """Plain text for one user's daily reminder. Shared-secret protected; read via docker exec."""
        expected = os.environ.get("DIGEST_TOKEN", "")
        if not expected or not hmac.compare_digest(token.encode(), expected.encode()):
            raise HTTPException(403, "forbidden")
        with db.scope() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (user.strip().lower(),)).fetchone()
            if row is None:
                raise errors.NotFound("no such user")
            return digest_view.digest(conn, dict(row))

    @app.get("/healthz", response_class=PlainTextResponse)
    def healthz():
        with db.scope() as conn:
            n = conn.execute("SELECT COUNT(*) AS n FROM items").fetchone()["n"]
        return f"ok {n} items"

    app.add_middleware(CacheHeaders)

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        """Serve a built file if it exists, otherwise the app shell for client-side routes.

        Resolves inside DIST only: a path that escapes it (../) falls through to the shell.
        """
        if path.startswith("api/"):
            raise HTTPException(404, "no such endpoint")
        # A missing build asset is a real 404, never the HTML shell: after a deploy a
        # stale tab may ask for an old chunk, and the shell must not be cached as code.
        if path.startswith("assets/") or path.startswith("fonts/"):
            candidate = (DIST / path).resolve()
            if candidate.is_file() and DIST.resolve() in candidate.parents:
                return FileResponse(candidate)
            raise HTTPException(404, "no such asset")
        if path:
            candidate = (DIST / path).resolve()
            if candidate.is_file() and DIST.resolve() in candidate.parents:
                return FileResponse(candidate)
        index = DIST / "index.html"
        if not index.is_file():
            raise HTTPException(503, "front end not built; run npm run build in frontend/")
        return FileResponse(index, media_type="text/html")

    return app


app = create_app()
