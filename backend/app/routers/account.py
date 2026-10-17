"""Account settings, password, deletion and the list switcher."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from .. import auth, db
from ..deps import Principal, clear_session_cookie, current_user
from ..services import account

router = APIRouter(prefix="/account")


class SettingsBody(BaseModel):
    preferred_list: Literal["plan", "sde", "a2z"] = "plan"
    timezone: str = Field(default="", max_length=64)
    weekly_sessions: int = Field(default=5, ge=3, le=7)
    design_sessions: int = Field(default=3, ge=0, le=7)
    design_minutes: Literal[15, 30, 45, 60] = 30


class PasswordBody(BaseModel):
    current_password: str = Field(max_length=1024)
    new_password: str = Field(max_length=1024)


class DeleteBody(BaseModel):
    password: str = Field(max_length=1024)


@router.post("/settings")
def post_settings(body: SettingsBody, principal: Principal = Depends(current_user)):
    # Only the fields the client sent: a partial body must not reset the others to defaults.
    with db.scope() as conn:
        return {"user": account.update_settings(conn, principal.user, body.model_dump(exclude_unset=True))}


@router.post("/password", status_code=204, response_class=Response)
def post_password(body: PasswordBody, principal: Principal = Depends(current_user)):
    with db.scope() as conn:
        auth.change_password(conn, principal.user, body.current_password, body.new_password, principal.token)


@router.post("/delete", status_code=204, response_class=Response)
def post_delete(body: DeleteBody, response: Response, principal: Principal = Depends(current_user)):
    with db.scope() as conn:
        auth.delete_account(conn, principal.user, body.password)
    clear_session_cookie(response)


@router.get("/lists")
def get_lists(principal: Principal = Depends(current_user)):
    with db.scope() as conn:
        return account.account_lists(conn, principal.user)
