"""Class-vs-class contest (班级对抗赛) workflows.

A contest owns two regular assignments (one per class) so submissions and
reviews keep using the existing assignment endpoints. Contest entries select
which students take part and which assignment side they belong to.
"""
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.schemas.common import success_response
from app.models.entities import (
    Assignment, AssignmentReview, AssignmentSubmission, ClassMember, Contest,
    ContestEntry, SysUser, TeacherClass,
)

router = APIRouter(tags=["班级对抗赛"])

TOOL_TYPES = Literal["SHADOW_PUPPET", "BRONZE_PATTERN", "LACQUER"]


def _owned_class(db: Session, class_id: int, user: dict) -> TeacherClass:
    query = db.query(TeacherClass).filter(TeacherClass.id == class_id)
    if user["role_code"] != "ADMIN":
        query = query.filter(TeacherClass.teacher_id == user["user_id"])
    record = query.first()
    if not record:
        raise HTTPException(404, "班级不存在或无权访问")
    return record


def _owned_contest(db: Session, contest_id: int, user: dict) -> Contest:
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(404, "对抗赛不存在")
    _owned_class(db, contest.home_class_id, user)
    _owned_class(db, contest.away_class_id, user)
    return contest


def _class_name(db: Session, class_id: int) -> str:
    record = db.get(TeacherClass, class_id)
    return record.name if record else ""


def _active_students(db: Session, class_id: int):
    return db.query(SysUser).join(
        ClassMember, ClassMember.student_id == SysUser.id
    ).filter(
        ClassMember.class_id == class_id,
        ClassMember.status == "ACTIVE",
        SysUser.status == "ACTIVE",
        SysUser.role_code == "STUDENT",
    ).order_by(SysUser.id).all()


def _validated_roster(db: Session, class_id: int, student_ids: list[int]) -> list[SysUser]:
    if len(set(student_ids)) != len(student_ids):
        raise HTTPException(409, "参赛名单中有重复学生")
    rows = db.query(SysUser).join(
        ClassMember, ClassMember.student_id == SysUser.id
    ).filter(
        SysUser.id.in_(student_ids),
        ClassMember.class_id == class_id,
        ClassMember.status == "ACTIVE",
        SysUser.status == "ACTIVE",
        SysUser.role_code == "STUDENT",
    ).all()
    found = {row.id: row for row in rows}
    missing = [sid for sid in student_ids if sid not in found]
    if missing:
        raise HTTPException(409, "参赛名单包含非本班在册学生")
    return [found[sid] for sid in student_ids]


def _submission_for(db: Session, assignment_id: int, student_id: int):
    return db.query(AssignmentSubmission).filter_by(
        assignment_id=assignment_id, student_id=student_id
    ).first()


def _review_for(db: Session, submission):
    if not submission:
        return None
    return db.query(AssignmentReview).filter_by(submission_id=submission.id).first()


def _entry_rows(db: Session, contest: Contest) -> list[dict]:
    entries = db.query(ContestEntry).filter(
        ContestEntry.contest_id == contest.id
    ).order_by(ContestEntry.class_id, ContestEntry.id).all()
    students = {
        user.id: user for user in db.query(SysUser).filter(
            SysUser.id.in_([entry.student_id for entry in entries])
        ).all()
    } if entries else {}
    rows = []
    for entry in entries:
        submission = _submission_for(db, entry.assignment_id, entry.student_id)
        review = _review_for(db, submission)
        student = students.get(entry.student_id)
        rows.append({
            "entry_id": entry.id,
            "class_id": entry.class_id,
            "student_id": entry.student_id,
            "student_name": student.nickname if student else f"学生{entry.student_id}",
            "avatar_url": student.avatar_url if student else "",
            "assignment_id": entry.assignment_id,
            "submission_id": submission.id if submission else None,
            "asset_id": submission.asset_id if submission else None,
            "source_task_id": submission.source_task_id if submission else None,
            "content": submission.content if submission else "",
            "submitted": submission is not None,
            "submitted_at": submission.submitted_at.isoformat() if submission and submission.submitted_at else None,
            "status": submission.status if submission else "NOT_SUBMITTED",
            "score": review.score if review else None,
            "comment": review.comment if review else None,
            "rank": None,
        })
    return rows


def _rank_students(rows: list[dict]) -> None:
    scored = sorted(
        [row for row in rows if row["score"] is not None],
        key=lambda row: (-row["score"], row["student_id"]),
    )
    previous = object()
    rank = 0
    for index, row in enumerate(scored):
        if row["score"] != previous:
            rank = index + 1
            previous = row["score"]
        row["rank"] = rank


def _class_summary(contest: Contest, class_id: int, name: str, rows: list[dict]) -> dict:
    scores = [row["score"] for row in rows if row["score"] is not None]
    total = sum(scores) if scores else None
    average = round(total / len(scores), 1) if scores else None
    metric = total if contest.scoring_mode == "TOTAL" else average
    return {
        "class_id": class_id,
        "name": name,
        "participant_count": len(rows),
        "submitted_count": sum(1 for row in rows if row["submitted"]),
        "scored_count": len(scores),
        "unsubmitted_count": sum(1 for row in rows if not row["submitted"]),
        "unscored_count": sum(1 for row in rows if row["submitted"] and row["score"] is None),
        "total_score": total,
        "average_score": average,
        "metric": metric,
        "rank": None,
        "entries": rows,
    }


def _build_contest(db: Session, contest: Contest) -> dict:
    home = db.get(TeacherClass, contest.home_class_id)
    away = db.get(TeacherClass, contest.away_class_id)
    rows = _entry_rows(db, contest)
    home_rows = [row for row in rows if row["class_id"] == contest.home_class_id]
    away_rows = [row for row in rows if row["class_id"] == contest.away_class_id]
    _rank_students(home_rows)
    _rank_students(away_rows)
    home_summary = _class_summary(contest, contest.home_class_id, home.name if home else "", home_rows)
    away_summary = _class_summary(contest, contest.away_class_id, away.name if away else "", away_rows)

    complete = home_summary["scored_count"] > 0 and away_summary["scored_count"] > 0
    winner = None
    if complete:
        if home_summary["metric"] > away_summary["metric"]:
            winner = contest.home_class_id
        elif away_summary["metric"] > home_summary["metric"]:
            winner = contest.away_class_id
    ranked = sorted(
        [home_summary, away_summary],
        key=lambda item: (
            -(item["metric"] if item["metric"] is not None else -1),
            -item["scored_count"],
            -item["submitted_count"],
            item["class_id"],
        ),
    )
    for index, item in enumerate(ranked):
        item["rank"] = index + 1 if item["metric"] is not None else None

    return {
        "id": contest.id,
        "title": contest.title,
        "description": contest.description,
        "tool_type": contest.tool_type,
        "round_no": contest.round_no,
        "scoring_mode": contest.scoring_mode,
        "deadline": contest.deadline.isoformat() if contest.deadline else None,
        "status": contest.status,
        "published_at": contest.published_at.isoformat() if contest.published_at else None,
        "created_at": contest.created_at.isoformat() if contest.created_at else None,
        "home_class": {"id": contest.home_class_id, "name": home.name if home else ""},
        "away_class": {"id": contest.away_class_id, "name": away.name if away else ""},
        "home_assignment_id": contest.home_assignment_id,
        "away_assignment_id": contest.away_assignment_id,
        "classes": [home_summary, away_summary],
        "winner_class_id": winner,
        "participant_count": len(rows),
        "submitted_count": home_summary["submitted_count"] + away_summary["submitted_count"],
        "scored_count": home_summary["scored_count"] + away_summary["scored_count"],
        "unsubmitted_count": home_summary["unsubmitted_count"] + away_summary["unsubmitted_count"],
        "unscored_count": home_summary["unscored_count"] + away_summary["unscored_count"],
        "can_edit_roster": contest.status == "OPEN",
        "can_publish": contest.status in ("OPEN", "SCORING"),
    }


def _student_contest(db: Session, contest: Contest, student_id: int) -> dict | None:
    entry = db.query(ContestEntry).filter_by(
        contest_id=contest.id, student_id=student_id
    ).first()
    if not entry:
        return None
    rows = _entry_rows(db, contest)
    own_rows = [row for row in rows if row["class_id"] == entry.class_id]
    _rank_students(own_rows)
    own_row = next(row for row in own_rows if row["student_id"] == student_id)
    other_class_id = (
        contest.away_class_id if entry.class_id == contest.home_class_id
        else contest.home_class_id
    )
    other_rows = [row for row in rows if row["class_id"] == other_class_id]
    _rank_students(other_rows)
    own_class = db.get(TeacherClass, entry.class_id)
    other_class = db.get(TeacherClass, other_class_id)
    published = contest.status == "PUBLISHED"

    def summary(class_id, name, class_rows):
        scored = [row["score"] for row in class_rows if row["score"] is not None]
        total = sum(scored) if scored else None
        return {
            "class_id": class_id,
            "name": name,
            "participant_count": len(class_rows),
            "submitted_count": sum(1 for row in class_rows if row["submitted"]),
            "scored_count": len(scored),
            "total_score": total if published else None,
            "average_score": round(total / len(scored), 1) if published and scored else None,
        }

    return {
        "id": contest.id,
        "title": contest.title,
        "description": contest.description,
        "tool_type": contest.tool_type,
        "round_no": contest.round_no,
        "deadline": contest.deadline.isoformat() if contest.deadline else None,
        "status": contest.status,
        "published": published,
        "published_at": contest.published_at.isoformat() if contest.published_at else None,
        "my_class": {"id": entry.class_id, "name": own_class.name if own_class else ""},
        "opponent_class": {"id": other_class_id, "name": other_class.name if other_class else ""},
        "my_entry": {
            "student_id": student_id,
            "assignment_id": entry.assignment_id,
            "submitted": own_row["submitted"],
            "submitted_at": own_row["submitted_at"],
            "status": own_row["status"],
            "content": own_row["content"],
            "asset_id": own_row["asset_id"],
            "source_task_id": own_row["source_task_id"],
            "score": own_row["score"] if published else None,
            "comment": own_row["comment"] if published else None,
            "rank": own_row["rank"] if published else None,
        },
        "my_class_summary": summary(entry.class_id, own_class.name if own_class else "", own_rows),
        "opponent_summary": summary(other_class_id, other_class.name if other_class else "", other_rows),
        "winner_class_id": (
            _build_contest(db, contest)["winner_class_id"] if published else None
        ),
    }


class ContestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=10000)
    tool_type: TOOL_TYPES = "SHADOW_PUPPET"
    home_class_id: int = Field(gt=0)
    away_class_id: int = Field(gt=0)
    round_no: int = Field(1, ge=1, le=99)
    scoring_mode: Literal["TOTAL", "AVERAGE"] = "TOTAL"
    deadline_days: int = Field(7, ge=1, le=365)
    home_student_ids: list[int] = Field(min_length=1, max_length=200)
    away_student_ids: list[int] = Field(min_length=1, max_length=200)

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class RosterUpdate(BaseModel):
    home_student_ids: list[int] | None = Field(None, max_length=200)
    away_student_ids: list[int] | None = Field(None, max_length=200)


class StatusUpdate(BaseModel):
    status: Literal["SCORING", "PUBLISHED"]


@router.get("/teacher/contests")
def list_teacher_contests(
    class_id: int | None = Query(None, gt=0),
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    query = db.query(Contest)
    if current_user["role_code"] != "ADMIN":
        query = query.filter(Contest.teacher_id == current_user["user_id"])
    if class_id:
        _owned_class(db, class_id, current_user)
        query = query.filter(
            (Contest.home_class_id == class_id) | (Contest.away_class_id == class_id)
        )
    contests = query.order_by(Contest.created_at.desc(), Contest.id.desc()).all()
    return success_response([
        {
            "id": contest.id,
            "title": contest.title,
            "round_no": contest.round_no,
            "status": contest.status,
            "deadline": contest.deadline.isoformat() if contest.deadline else None,
            "home_class": {"id": contest.home_class_id, "name": _class_name(db, contest.home_class_id)},
            "away_class": {"id": contest.away_class_id, "name": _class_name(db, contest.away_class_id)},
            "submitted_count": db.query(AssignmentSubmission).filter(
                AssignmentSubmission.assignment_id.in_(
                    [contest.home_assignment_id, contest.away_assignment_id]
                )
            ).count() if contest.home_assignment_id and contest.away_assignment_id else 0,
            "winner_class_id": (contest.result_json or {}).get("winner_class_id"),
        }
        for contest in contests
    ])


@router.post("/teacher/contests")
def create_contest(
    req: ContestCreate,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    if req.home_class_id == req.away_class_id:
        raise HTTPException(409, "对抗赛必须选择两个不同班级")
    home = _owned_class(db, req.home_class_id, current_user)
    away = _owned_class(db, req.away_class_id, current_user)
    home_students = _validated_roster(db, home.id, req.home_student_ids)
    away_students = _validated_roster(db, away.id, req.away_student_ids)
    overlap = {student.id for student in home_students} & {student.id for student in away_students}
    if overlap:
        raise HTTPException(409, "同一学生不能同时代表两个班级参赛")

    deadline = datetime.utcnow() + timedelta(days=req.deadline_days)
    contest = Contest(
        teacher_id=home.teacher_id,
        title=req.title,
        description=req.description,
        tool_type=req.tool_type,
        home_class_id=home.id,
        away_class_id=away.id,
        round_no=req.round_no,
        scoring_mode=req.scoring_mode,
        deadline=deadline,
        status="OPEN",
    )
    db.add(contest)
    db.flush()

    home_assignment = Assignment(
        class_id=home.id,
        teacher_id=home.teacher_id,
        title=req.title,
        type="CONTEST",
        tool_type=req.tool_type,
        deadline=deadline,
        description=req.description,
        status="PUBLISHED",
        contest_id=contest.id,
    )
    away_assignment = Assignment(
        class_id=away.id,
        teacher_id=away.teacher_id,
        title=req.title,
        type="CONTEST",
        tool_type=req.tool_type,
        deadline=deadline,
        description=req.description,
        status="PUBLISHED",
        contest_id=contest.id,
    )
    db.add_all([home_assignment, away_assignment])
    db.flush()
    contest.home_assignment_id = home_assignment.id
    contest.away_assignment_id = away_assignment.id
    for student in home_students:
        db.add(ContestEntry(contest_id=contest.id, class_id=home.id,
                            student_id=student.id, assignment_id=home_assignment.id))
    for student in away_students:
        db.add(ContestEntry(contest_id=contest.id, class_id=away.id,
                            student_id=student.id, assignment_id=away_assignment.id))
    db.commit()
    db.refresh(contest)
    return success_response(_build_contest(db, contest), message="对抗赛已创建")


@router.get("/teacher/contests/{contest_id}")
def get_teacher_contest(
    contest_id: int,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    contest = _owned_contest(db, contest_id, current_user)
    return success_response(_build_contest(db, contest))


@router.put("/teacher/contests/{contest_id}/entries")
def update_contest_entries(
    contest_id: int,
    req: RosterUpdate,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    contest = _owned_contest(db, contest_id, current_user)
    if contest.status != "OPEN":
        raise HTTPException(409, "对抗赛已截止，参赛名单不可修改")
    sides = [
        (req.home_student_ids, contest.home_class_id, contest.home_assignment_id),
        (req.away_student_ids, contest.away_class_id, contest.away_assignment_id),
    ]
    final_sets = {}
    for student_ids, class_id, assignment_id in sides:
        if student_ids is None:
            final_sets[class_id] = {
                entry.student_id for entry in db.query(ContestEntry).filter_by(
                    contest_id=contest.id, class_id=class_id
                ).all()
            }
        else:
            final_sets[class_id] = set(student_ids)
    if final_sets[contest.home_class_id] & final_sets[contest.away_class_id]:
        raise HTTPException(409, "同一学生不能同时代表两个班级参赛")
    for student_ids, class_id, assignment_id in sides:
        if student_ids is None:
            continue
        students = _validated_roster(db, class_id, student_ids)
        current_entries = db.query(ContestEntry).filter_by(
            contest_id=contest.id, class_id=class_id
        ).all()
        current_by_student = {entry.student_id: entry for entry in current_entries}
        requested = {student.id for student in students}
        for student_id, entry in current_by_student.items():
            if student_id in requested:
                continue
            if _submission_for(db, assignment_id, student_id):
                raise HTTPException(409, "已有学生提交，不能将其移出参赛名单")
            db.delete(entry)
        for student in students:
            if student.id not in current_by_student:
                db.add(ContestEntry(contest_id=contest.id, class_id=class_id,
                                    student_id=student.id, assignment_id=assignment_id))
    db.commit()
    return success_response(_build_contest(db, contest), message="参赛名单已更新")


@router.post("/teacher/contests/{contest_id}/status")
def update_contest_status(
    contest_id: int,
    req: StatusUpdate,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    contest = db.query(Contest).filter(Contest.id == contest_id).with_for_update().first()
    if not contest:
        raise HTTPException(404, "对抗赛不存在")
    _owned_class(db, contest.home_class_id, current_user)
    _owned_class(db, contest.away_class_id, current_user)
    if contest.status == "PUBLISHED":
        if req.status == "PUBLISHED":
            return success_response(_build_contest(db, contest), message="成绩已公布")
        raise HTTPException(409, "成绩已公布，不能回退状态")
    if req.status == "SCORING":
        if contest.status == "SCORING":
            return success_response(_build_contest(db, contest), message="已进入评分阶段")
        contest.status = "SCORING"
        db.commit()
        return success_response(_build_contest(db, contest), message="提交已截止，进入评分阶段")

    rows = _entry_rows(db, contest)
    if not any(row["score"] is not None for row in rows):
        raise HTTPException(409, "至少需要一个已评分作品才能公布成绩")
    contest.status = "PUBLISHED"
    contest.published_at = datetime.utcnow()
    detail = _build_contest(db, contest)
    contest.result_json = {
        "published_at": contest.published_at.isoformat(),
        "scoring_mode": contest.scoring_mode,
        "winner_class_id": detail["winner_class_id"],
        "classes": [
            {
                "class_id": item["class_id"],
                "total_score": item["total_score"],
                "average_score": item["average_score"],
                "scored_count": item["scored_count"],
                "rank": item["rank"],
                "scores": [
                    {"student_id": entry["student_id"], "score": entry["score"], "rank": entry["rank"]}
                    for entry in item["entries"] if entry["score"] is not None
                ],
            }
            for item in detail["classes"]
        ],
    }
    db.commit()
    return success_response(_build_contest(db, contest), message="成绩已公布并锁定")


@router.get("/mobile/me/contests")
def list_my_contests(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role_code"] != "STUDENT":
        raise HTTPException(403, "仅学生可查看参赛记录")
    entries = db.query(ContestEntry).filter(
        ContestEntry.student_id == current_user["user_id"]
    ).order_by(ContestEntry.id.desc()).all()
    contest_ids = [entry.contest_id for entry in entries]
    contests = {
        contest.id: contest for contest in db.query(Contest).filter(
            Contest.id.in_(contest_ids)
        ).all()
    } if contest_ids else {}
    result = []
    for entry in entries:
        contest = contests.get(entry.contest_id)
        if not contest:
            continue
        submission = _submission_for(db, entry.assignment_id, current_user["user_id"])
        review = _review_for(db, submission)
        published = contest.status == "PUBLISHED"
        other_class_id = (
            contest.away_class_id if entry.class_id == contest.home_class_id
            else contest.home_class_id
        )
        other_class = db.get(TeacherClass, other_class_id)
        result.append({
            "id": contest.id,
            "title": contest.title,
            "round_no": contest.round_no,
            "status": contest.status,
            "deadline": contest.deadline.isoformat() if contest.deadline else None,
            "my_class": {"id": entry.class_id, "name": _class_name(db, entry.class_id)},
            "opponent_class": {"id": other_class_id, "name": other_class.name if other_class else ""},
            "submitted": submission is not None,
            "score": review.score if published and review else None,
            "rank": None,
            "winner_class_id": (contest.result_json or {}).get("winner_class_id") if published else None,
        })
    return success_response(result)


@router.get("/mobile/me/contests/{contest_id}")
def get_my_contest(
    contest_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role_code"] != "STUDENT":
        raise HTTPException(403, "仅学生可查看参赛记录")
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(404, "对抗赛不存在")
    detail = _student_contest(db, contest, current_user["user_id"])
    if not detail:
        raise HTTPException(404, "您不在本轮参赛名单中")
    return success_response(detail)
