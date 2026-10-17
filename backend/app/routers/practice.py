"""The practice screens and every write on a user's progress. All scoped to the signed-in user."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from .. import db
from ..deps import Principal, current_user
from ..services import design, items, plan, problems, reset, stats, today

router = APIRouter()


@router.get("/today")
def get_today(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return today.today(conn, p.user)


@router.get("/problems")
def get_problems(view: Literal["plan", "sde", "a2z"] = "plan", p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return problems.problems(conn, p.user, view)


@router.get("/design")
def get_design(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return design.design(conn, p.user)


@router.get("/plan")
def get_plan(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return plan.plan(conn, p.user)


@router.get("/stats")
def get_stats(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return stats.stats(conn, p.user)


@router.get("/items/{item_id}")
def get_item(item_id: int, p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return items.item_detail(conn, p.user, item_id)


class LogBody(BaseModel):
    item_id: int
    mode: Literal["learn", "solve", "resolve", "recall", "rebuild", "mock"] = "solve"
    score: int | None = Field(default=None, ge=0, le=3)
    minutes: int | None = Field(default=None, ge=1, le=600)
    note: str = Field(default="", max_length=2000)
    independent: bool | None = None


class ReviewBody(BaseModel):
    outcome: Literal["pass", "fail"]
    note: str = Field(default="", max_length=2000)


class DecisionBody(BaseModel):
    item_id: int
    chose: str = Field(min_length=1, max_length=500)
    rejected: str = Field(default="", max_length=500)
    because: str = Field(default="", max_length=500)


class ResetBody(BaseModel):
    scope: Literal["week", "plan", "sde", "a2z", "design", "item", "all"]
    item_id: int | None = None


@router.post("/log")
def post_log(body: LogBody, p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return items.log_attempt(conn, p.user, body.item_id, body.mode, body.score, body.minutes, body.note, body.independent)


@router.post("/reviews/spread")
def post_spread(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return items.spread_overdue(conn, p.user)


@router.post("/reviews/{review_id}")
def post_review(review_id: int, body: ReviewBody, p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return items.complete_review(conn, p.user, review_id, body.outcome, body.note)


@router.post("/items/{item_id}/star")
def post_star(item_id: int, p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return items.toggle_star(conn, p.user, item_id)


@router.post("/decisions")
def post_decision(body: DecisionBody, p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return items.add_decision(conn, p.user, body.item_id, body.chose, body.rejected, body.because)


@router.get("/reset")
def get_reset(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return reset.reset_preview(conn, p.user)


@router.post("/reset")
def post_reset(body: ResetBody, p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return reset.reset(conn, p.user, body.scope, body.item_id)


@router.post("/reset/undo")
def post_reset_undo(p: Principal = Depends(current_user)):
    with db.scope() as conn:
        return reset.undo_reset(conn, p.user)
