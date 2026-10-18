from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.common import success_response
from app.models.entities import SysUser, Badge, UserBadge
from app.models.mobile import WalkSession
from app.api.activity import haversine_distance

router = APIRouter(prefix="/mobile/walks", tags=["前台研学计时与足迹"])


def today_bounds():
    start = datetime.now(ZoneInfo("Asia/Shanghai")).replace(hour=0, minute=0, second=0, microsecond=0)
    return (start.astimezone(timezone.utc).replace(tzinfo=None),
            (start + timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None))


def today_total(db, user_id):
    start, end = today_bounds()
    return int(db.query(func.coalesce(func.sum(WalkSession.active_seconds), 0)).filter(
        WalkSession.user_id == user_id, WalkSession.started_at >= start, WalkSession.started_at < end).scalar())


def serialize(record):
    return {"id": record.id, "active_seconds": record.active_seconds, "distance_meters": record.distance_meters,
            "status": record.status, "started_at": record.started_at.isoformat(),
            "ended_at": record.ended_at.isoformat() if record.ended_at else None}


@router.get("")
def history(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(WalkSession).filter_by(user_id=user["user_id"]).order_by(WalkSession.started_at.desc()).all()
    start, end = today_bounds()
    return success_response({"list": [serialize(r) for r in records],
                             "today_seconds": sum(r.active_seconds for r in records if start <= r.started_at < end),
                             "total_seconds": sum(r.active_seconds for r in records),
                             "total_distance_meters": sum(r.distance_meters for r in records)})


@router.post("")
def start(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SysUser).filter_by(id=user["user_id"]).with_for_update().one()
    record = db.query(WalkSession).filter_by(user_id=user["user_id"], status="ACTIVE").first()
    if record and record.started_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).date() != datetime.now(ZoneInfo("Asia/Shanghai")).date():
        record.status, record.ended_at = "COMPLETED", datetime.now(timezone.utc).replace(tzinfo=None)
        record = None
    if not record:
        record = WalkSession(user_id=user["user_id"])
        db.add(record); db.commit()
    return success_response(serialize(record))


class WalkReport(BaseModel):
    active_seconds: int = Field(ge=0, le=86400)
    latitude: float | None = Field(None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(None, ge=-180, le=180, allow_inf_nan=False)
    accuracy: float | None = Field(None, ge=0, le=10000, allow_inf_nan=False)
    completed: bool = False

    @model_validator(mode="after")
    def paired_coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("经纬度必须一起提供")
        return self


@router.put("/{walk_id}")
def report(walk_id: int, req: WalkReport, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SysUser).filter_by(id=user["user_id"]).with_for_update().one()
    record = db.query(WalkSession).filter_by(id=walk_id, user_id=user["user_id"]).with_for_update().first()
    if not record:
        raise HTTPException(404, "研学记录不存在")
    if record.status == "COMPLETED":
        return success_response(serialize(record))
    now = datetime.utcnow()
    start_day_end = (record.started_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Shanghai"))
                     .replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).astimezone(timezone.utc).replace(tzinfo=None)
    wall_seconds = max(0, int((min(now, start_day_end) - record.started_at).total_seconds()))
    record.active_seconds = max(record.active_seconds, min(req.active_seconds, wall_seconds))
    if req.latitude is not None and (req.accuracy is None or req.accuracy <= 100):
        if record.last_latitude is not None and record.last_point_at:
            delta = haversine_distance(float(record.last_latitude), float(record.last_longitude), req.latitude, req.longitude)
            elapsed = max(1, (now - record.last_point_at).total_seconds())
            # Ignore GPS jitter and implausible jumps instead of calling them walked distance.
            if 5 <= delta <= elapsed * 10:
                record.distance_meters += delta
        record.last_latitude, record.last_longitude, record.last_point_at = req.latitude, req.longitude, now
    if req.completed:
        record.status, record.ended_at = "COMPLETED", now
    db.flush()
    today_seconds = today_total(db, user["user_id"])
    badge_unlocked_code = None
    if today_seconds >= 3600:
        badge = db.query(Badge).filter_by(code="BADGE_WALK_PATHFINDER").first()
        if badge and not db.query(UserBadge).filter_by(user_id=user["user_id"], badge_id=badge.id).first():
            db.add(UserBadge(user_id=user["user_id"], badge_id=badge.id))
            badge_unlocked_code = badge.code
    db.commit()
    return success_response({**serialize(record), "badge_unlocked_code": badge_unlocked_code})
