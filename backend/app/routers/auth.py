"""Sign up, sign in, sign out. The only /api routes that work without a session."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from .. import auth, db
from ..deps import Principal, clear_session_cookie, current_user, set_session_cookie

router = APIRouter(prefix="/auth")


class RegisterBody(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=1024)
    timezone: str = Field(max_length=64)
    preferred_list: Literal["plan", "sde", "a2z"] = "plan"


class LoginBody(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=1024)


@router.get("/status")
def get_status():
    with db.scope() as conn:
        return auth.status(conn)


@router.get("/me")
def get_me(principal: Principal = Depends(current_user)):
    return {"user": auth.user_dto(principal.user)}


@router.post("/register", status_code=201)
def post_register(body: RegisterBody, response: Response):
    with db.scope() as conn:
        user, token = auth.register(conn, body.username, body.password, body.timezone, body.preferred_list)
    set_session_cookie(response, token)
    return {"user": auth.user_dto(user)}


@router.post("/login")
def post_login(body: LoginBody, response: Response):
    with db.scope() as conn:
        user, token = auth.login(conn, body.username, body.password)
    set_session_cookie(response, token)
    return {"user": auth.user_dto(user)}


@router.post("/logout", status_code=204, response_class=Response)
def post_logout(request: Request, response: Response):
    token = request.cookies.get(auth.COOKIE_NAME, "")
    if token:
        with db.scope() as conn:
            auth.end_session(conn, token)
    clear_session_cookie(response)
