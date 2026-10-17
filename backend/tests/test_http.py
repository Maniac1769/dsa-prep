"""The real routes, driven through the ASGI app: cookies, status codes, and isolation over HTTP."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from app import auth, db, errors, main
from app.deps import current_user, same_site_write

from .asgi import Client
from .support import SEED

PASSWORD = "correct horse battery"


class HttpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "prep.db"
        db.SEED_DIR = SEED
        with db.scope() as conn:
            db.init(conn)
            db.seed(conn)
        auth.reset_throttle()
        self.app = main.create_app()
        env = mock.patch.dict(os.environ, {"MAX_USERS": "20", "DIGEST_TOKEN": "tok"})
        env.start()
        self.addCleanup(env.stop)
        quiet = mock.patch("builtins.print")
        quiet.start()
        self.addCleanup(quiet.stop)
        self.addCleanup(self.tmp.cleanup)

    def client(self) -> Client:
        return Client(self.app)

    def signed_in(self, name: str = "asha", **extra) -> Client:
        c = self.client()
        r = c.post("/api/auth/register", {"username": name, "password": PASSWORD, "timezone": "Asia/Kolkata", **extra})
        self.assertEqual(r.status, 201, r.text())
        return c

    # --- the guards ---------------------------------------------------------------------

    def test_every_api_route_but_auth_needs_a_session_and_every_post_the_header(self) -> None:
        from fastapi.routing import APIRoute

        def calls(dependant):
            for d in dependant.dependencies:
                yield d.call
                yield from calls(d)

        checked = 0
        for route in self.app.routes:
            if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
                continue
            found = set(calls(route.dependant))
            if not route.path.startswith("/api/auth/"):
                self.assertIn(current_user, found, route.path)
            if "POST" in route.methods:
                self.assertIn(same_site_write, found, route.path)
            checked += 1
        self.assertGreater(checked, 20)

    def test_unauthenticated_requests(self) -> None:
        c = self.client()
        for path in ("/api/today", "/api/plan", "/api/stats", "/api/design", "/api/problems", "/api/reset",
                     "/api/items/1", "/api/account/lists", "/api/auth/me"):
            self.assertEqual(c.get(path).status, 401, path)
        for path in ("/api/log", "/api/reset", "/api/reset/undo", "/api/items/1/star", "/api/decisions",
                     "/api/reviews/spread", "/api/reviews/1", "/api/account/settings", "/api/account/password",
                     "/api/account/delete"):
            self.assertEqual(c.post(path, {}).status, 401, path)

    def test_a_write_without_the_header_is_403_before_anything_else(self) -> None:
        c = self.signed_in()
        for path in ("/api/reset", "/api/log", "/api/auth/login", "/api/auth/register", "/api/auth/logout",
                     "/api/account/delete"):
            self.assertEqual(c.post(path, {"scope": "all"}, prep=False).status, 403, path)
        self.assertEqual(self.client().post("/api/reset", {"scope": "all"}, prep=False).status, 403, "even signed out")

    # --- auth ---------------------------------------------------------------------------

    def test_register_sets_a_hardened_session_cookie(self) -> None:
        c = self.client()
        r = c.post("/api/auth/register", {"username": "Asha", "password": PASSWORD, "timezone": "Asia/Kolkata", "preferred_list": "sde"})
        self.assertEqual(r.status, 201)
        self.assertEqual(r.json()["user"]["username"], "asha")
        self.assertEqual(r.json()["user"]["preferred_list"], "sde")
        self.assertNotIn("password", r.text())
        cookie = r.set_cookies[0]
        for flag in ("HttpOnly", "SameSite=lax", "Path=/", "Max-Age=2592000", "Secure"):
            self.assertIn(flag, cookie)
        self.assertEqual(c.get("/api/auth/me").json()["user"]["username"], "asha")
        self.assertEqual(c.get("/api/today").status, 200)

    def test_a_session_under_fifteen_days_from_expiry_gets_a_fresh_cookie(self) -> None:
        c = self.signed_in()
        self.assertEqual(c.get("/api/today").set_cookies, [], "a fresh session is not re-sent")
        soon = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat(timespec="seconds")
        with db.scope() as conn:
            conn.execute("UPDATE auth_sessions SET expires_at = ?", (soon,))
            conn.commit()
        r = c.get("/api/today")
        self.assertEqual(r.status, 200)
        self.assertEqual(len(r.set_cookies), 1)
        for flag in ("prep_session=", "Max-Age=2592000", "HttpOnly", "SameSite=lax"):
            self.assertIn(flag, r.set_cookies[0])
        with db.scope() as conn:
            expires = conn.execute("SELECT expires_at FROM auth_sessions").fetchone()[0]
        self.assertGreater(datetime.fromisoformat(expires), datetime.now(timezone.utc) + timedelta(days=29))

    def test_cookie_is_not_secure_when_switched_off_for_local_dev(self) -> None:
        with mock.patch.dict(os.environ, {"COOKIE_SECURE": "0"}):
            r = self.client().post("/api/auth/register", {"username": "asha", "password": PASSWORD, "timezone": "UTC"})
        self.assertNotIn("Secure", r.set_cookies[0])

    def test_login_logout_roundtrip_and_clearing_the_cookie(self) -> None:
        self.signed_in()
        c = self.client()
        self.assertEqual(c.post("/api/auth/login", {"username": "ASHA", "password": PASSWORD}).status, 200)
        self.assertEqual(c.get("/api/today").status, 200)
        out = c.post("/api/auth/logout")
        self.assertEqual(out.status, 204)
        self.assertIn("Max-Age=0", out.set_cookies[0])
        self.assertEqual(c.get("/api/today").status, 401)

    def test_wrong_login_is_401_and_lockout_is_429_with_retry_after(self) -> None:
        self.signed_in()
        c = self.client()
        for _ in range(5):
            self.assertEqual(c.post("/api/auth/login", {"username": "asha", "password": "wrong password"}).status, 401)
        r = c.post("/api/auth/login", {"username": "asha", "password": PASSWORD})
        self.assertEqual(r.status, 429)
        self.assertGreater(int(r.headers["retry-after"]), 0)
        self.assertIn("detail", r.json())

    def test_status_is_public_and_reports_the_cap_and_lists(self) -> None:
        c = self.client()
        before = c.get("/api/auth/status").json()
        self.assertEqual((before["users"], before["cap"], before["registration_open"]), (0, 20, True))
        self.assertEqual([x["key"] for x in before["lists"]], ["plan", "sde", "a2z"])
        self.signed_in()
        self.assertEqual(c.get("/api/auth/status").json()["users"], 1)

    def test_sign_ups_stop_at_the_cap_with_403(self) -> None:
        with mock.patch.dict(os.environ, {"MAX_USERS": "1"}):
            self.signed_in("one")
            r = self.client().post("/api/auth/register", {"username": "two", "password": PASSWORD, "timezone": "UTC"})
        self.assertEqual((r.status, r.json()["detail"]), (403, "Sign-ups are full: 1 of 1 places taken."))

    def test_duplicate_username_is_409_and_bad_input_is_400(self) -> None:
        self.signed_in("asha")
        body = {"username": "ASHA", "password": PASSWORD, "timezone": "UTC"}
        self.assertEqual(self.client().post("/api/auth/register", body).status, 409)
        for bad in ({**body, "username": "a"}, {**body, "password": "short"}, {**body, "timezone": "Mars/Base"},
                    {**body, "preferred_list": "nope"}, {"username": "x"}):
            r = self.client().post("/api/auth/register", bad)
            self.assertEqual(r.status, 400, bad)
            self.assertIsInstance(r.json()["detail"], str)

    def test_password_change_signs_out_other_devices_only(self) -> None:
        here = self.signed_in()
        there = self.client()
        there.post("/api/auth/login", {"username": "asha", "password": PASSWORD})
        r = here.post("/api/account/password", {"current_password": PASSWORD, "new_password": "another good passphrase"})
        self.assertEqual(r.status, 204)
        self.assertEqual(here.get("/api/today").status, 200)
        self.assertEqual(there.get("/api/today").status, 401)
        self.assertEqual(self.client().post("/api/auth/login", {"username": "asha", "password": PASSWORD}).status, 401)

    def test_delete_account_needs_the_password_and_removes_everything(self) -> None:
        c = self.signed_in()
        first = c.get("/api/today").json()["focus"]["id"]
        c.post("/api/log", {"item_id": first, "mode": "solve", "score": 2})
        self.assertEqual(c.post("/api/account/delete", {"password": "wrong password"}).status, 403)
        out = c.post("/api/account/delete", {"password": PASSWORD})
        self.assertEqual(out.status, 204)
        self.assertIn("Max-Age=0", out.set_cookies[0])
        with db.scope() as conn:
            for table in ("users", "attempts", "reviews", "auth_sessions"):
                self.assertEqual(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 0, table)

    # --- isolation over HTTP ----------------------------------------------------------------

    def test_two_users_over_http(self) -> None:
        a, b = self.signed_in("asha"), self.signed_in("ravi")
        first = a.get("/api/today").json()["focus"]["id"]
        self.assertEqual(a.post("/api/log", {"item_id": first, "mode": "solve", "score": 3}).status, 200)
        review = a.get(f"/api/items/{first}").json()["reviews"][0]["id"]

        self.assertEqual(b.get(f"/api/items/{first}").json()["attempts"], [])
        self.assertEqual(b.get("/api/stats").json()["any_activity"], False)
        self.assertEqual(b.post(f"/api/reviews/{review}", {"outcome": "pass"}).status, 404)
        self.assertEqual(b.post("/api/reset", {"scope": "all"}).json()["attempts"], 0)
        self.assertEqual(b.post("/api/reset/undo").status, 200)  # B's own (empty) reset
        self.assertEqual(a.get(f"/api/items/{first}").json()["item"]["status"], "solid")
        self.assertEqual(a.post("/api/reset/undo").status, 409, "A never reset, so A has nothing to undo")

        a.post("/api/reset", {"scope": "all"})
        self.assertEqual(b.get("/api/reset").json()["undo"], None)
        self.assertEqual(a.post("/api/reset/undo").status, 200)
        self.assertEqual(a.get(f"/api/items/{first}").json()["item"]["status"], "solid")

    def test_settings_update_is_partial_and_validated(self) -> None:
        c = self.signed_in()
        user = c.post("/api/account/settings", {"weekly_sessions": 4}).json()["user"]
        self.assertEqual((user["weekly_sessions"], user["design_sessions"], user["preferred_list"]), (4, 3, "plan"))
        for bad in ({"weekly_sessions": 9}, {"design_minutes": 20}, {"preferred_list": "x"}, {"timezone": "Nope/Nope"}):
            self.assertEqual(c.post("/api/account/settings", bad).status, 400, bad)
        self.assertEqual(c.get("/api/account/lists").json()["lists"][0]["preferred"], True)
        c.post("/api/account/settings", {"preferred_list": "a2z"})
        self.assertEqual([x["preferred"] for x in c.get("/api/account/lists").json()["lists"]], [False, False, True])

    def test_problems_views_for_all_three_lists(self) -> None:
        c = self.signed_in()
        for view in ("plan", "sde", "a2z"):
            r = c.get(f"/api/problems?view={view}")
            self.assertEqual(r.status, 200, view)
            self.assertEqual(len(r.json()["lists"]), 3)
        self.assertEqual(c.get("/api/problems?view=nope").status, 400)

    def test_log_accepts_recall_and_rejects_unknown_modes(self) -> None:
        c = self.signed_in()
        first = c.get("/api/today").json()["focus"]["id"]
        self.assertEqual(c.post("/api/log", {"item_id": first, "mode": "recall"}).status, 200)
        self.assertEqual(c.post("/api/log", {"item_id": first, "mode": "nap"}).status, 400)
        self.assertEqual(c.get("/api/today").json()["session"]["short_days"], 1)

    def test_digest_is_per_user_and_token_protected(self) -> None:
        c = self.signed_in("asha")
        self.assertEqual(c.get("/digest?token=wrong&user=asha").status, 403)
        self.assertEqual(c.get("/digest?token=tok&user=nobody").status, 404)
        r = c.get("/digest?token=tok&user=ASHA")
        self.assertEqual(r.status, 200)
        self.assertIn("session 1 of 5", r.text())

    def test_every_error_type_maps_to_its_status(self) -> None:
        self.assertEqual(
            {k.__name__: v for k, v in main.STATUS.items()},
            {"NotFound": 404, "Invalid": 400, "Conflict": 409, "Unauthorized": 401, "Forbidden": 403, "TooMany": 429},
        )
        reply = main._error_response(None, errors.TooMany("slow down", 7))
        self.assertEqual((reply.status_code, reply.headers["retry-after"]), (429, "7"))

    def test_unknown_api_path_is_404(self) -> None:
        self.assertEqual(self.signed_in().get("/api/nope").status, 404)

    def test_healthz(self) -> None:
        self.assertTrue(self.client().get("/healthz").text().startswith("ok "))


if __name__ == "__main__":
    unittest.main()
