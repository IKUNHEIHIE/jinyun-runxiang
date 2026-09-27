from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, hash_password, verify_password
from app.schemas.common import success_response, error_response
from app.models.entities import (
    HeritageLandmark, Activity, ActivityReservation, ActivityAttendance,
    GrowthEvent, UserGrowth, Badge, UserBadge
)

router = APIRouter(prefix="/activities", tags=["非遗活动与现场签到"])


class CreateActivityRequest(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    type: Literal["OFFLINE", "LIVE", "CHALLENGE"] = "OFFLINE"
    master_name: Optional[str] = Field(default=None, max_length=64)
    start_at: datetime
    end_at: datetime
    capacity: int = Field(gt=0)
    energy_reward: int = Field(default=30, ge=0)
    badge_id: Optional[int] = None
    description: str = Field(min_length=1)
    status: Literal["DRAFT", "PUBLISHED"] = "DRAFT"


class CheckinCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=64)


class AttendRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)


def _utc_naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

class CheckinRequest(BaseModel):
    landmark_id: int
    activity_id: Optional[int] = None
    latitude: float
    longitude: float

@router.get("/landmarks")
def list_landmarks(district: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(HeritageLandmark).filter(HeritageLandmark.status == "ACTIVE")
    if district:
        query = query.filter(HeritageLandmark.district == district)
    landmarks = query.all()
    return success_response([{
        "id": l.id,
        "name": l.name,
        "category": l.category,
        "address": l.address,
        "district": l.district,
        "latitude": float(l.latitude),
        "longitude": float(l.longitude),
        "geofence_radius_meters": l.geofence_radius_meters,
        "description": l.description,
        "cover_url": l.cover_url
    } for l in landmarks])

@router.get("")
def list_activities(type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Activity).filter(Activity.status.in_(["PUBLISHED", "ONGOING"]))
    if type:
        query = query.filter(Activity.type == type)
    activities = query.order_by(Activity.start_at.asc()).all()

    return success_response([{
        "id": a.id,
        "title": a.title,
        "type": a.type,
        "master_name": a.master_name,
        "start_at": a.start_at.strftime("%Y-%m-%d %H:%M"),
        "end_at": a.end_at.strftime("%Y-%m-%d %H:%M"),
        "capacity": a.capacity,
        "reserved_count": a.reserved_count,
        "energy_reward": a.energy_reward,
        "description": a.description
    } for a in activities])


@router.post("")
def create_activity(
    req: CreateActivityRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    start_at, end_at = _utc_naive(req.start_at), _utc_naive(req.end_at)
    if end_at <= start_at:
        return error_response(code=4000, message="结束时间必须晚于开始时间")
    if req.badge_id is not None and not db.query(Badge).filter(Badge.id == req.badge_id).first():
        return error_response(code=4040, message="徽章不存在")
    activity = Activity(
        title=req.title, type=req.type, master_name=req.master_name,
        start_at=start_at, end_at=end_at, capacity=req.capacity,
        reserved_count=0, energy_reward=req.energy_reward,
        badge_id=req.badge_id, description=req.description, status=req.status
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return success_response({"id": activity.id, "status": activity.status}, message="活动已创建")


@router.put("/{activity_id}/checkin-code")
def set_activity_checkin_code(
    activity_id: int,
    req: CheckinCodeRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return error_response(code=4040, message="活动不存在")
    activity.checkin_code_hash = hash_password(req.code)
    db.commit()
    return success_response(message="现场签到码已设置")


@router.get("/my-reservations")
def list_my_reservations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reservations = db.query(ActivityReservation).filter(
        ActivityReservation.user_id == current_user["user_id"]
    ).all()
    return success_response([{
        "activity_id": reservation.activity_id,
        "status": reservation.status,
        "reserved_at": reservation.reserved_at
    } for reservation in reservations])


@router.get("/{activity_id}/stats")
def get_activity_stats(
    activity_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return error_response(code=4040, message="活动不存在")
    attended = db.query(ActivityAttendance).filter(ActivityAttendance.activity_id == activity_id).count()
    return success_response({
        "activity_id": activity_id,
        "capacity": activity.capacity,
        "reserved_count": activity.reserved_count,
        "attended_count": attended,
        "not_attended_count": max(0, (activity.reserved_count or 0) - attended)
    })

@router.post("/{activity_id}/reserve")
def reserve_activity(
    activity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    activity = db.query(Activity).filter(Activity.id == activity_id).with_for_update().first()
    if not activity:
        return error_response(code=4040, message="活动不存在")
    if activity.status not in ("PUBLISHED", "ONGOING") or datetime.utcnow() >= activity.start_at:
        return error_response(code=4090, message="活动不可预约")
    existing = db.query(ActivityReservation).filter(
        ActivityReservation.activity_id == activity_id,
        ActivityReservation.user_id == user_id
    ).first()
    if existing and existing.status in ("CONFIRMED", "ATTENDED"):
        return success_response({"activity_id": activity_id, "status": existing.status}, message="已预约该活动")
    if (activity.reserved_count or 0) >= activity.capacity:
        return error_response(code=4090, message="该活动预约名额已满")
    if existing:
        existing.status = "CONFIRMED"
        existing.reserved_at = datetime.utcnow()
    else:
        db.add(ActivityReservation(activity_id=activity_id, user_id=user_id, status="CONFIRMED"))
    activity.reserved_count = (activity.reserved_count or 0) + 1
    db.commit()

    return success_response({"activity_id": activity_id, "status": "CONFIRMED"}, message="预约成功")


@router.post("/{activity_id}/cancel-reservation")
def cancel_activity_reservation(
    activity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    activity = db.query(Activity).filter(Activity.id == activity_id).with_for_update().first()
    if not activity:
        return error_response(code=4040, message="活动不存在")
    reservation = db.query(ActivityReservation).filter(
        ActivityReservation.activity_id == activity_id,
        ActivityReservation.user_id == current_user["user_id"]
    ).first()
    if not reservation or reservation.status == "CANCELLED":
        return success_response({"activity_id": activity_id, "status": "CANCELLED"})
    if reservation.status != "CONFIRMED" or datetime.utcnow() >= activity.start_at:
        return error_response(code=4090, message="活动已开始或已签到，不能取消预约")
    reservation.status = "CANCELLED"
    activity.reserved_count = max(0, (activity.reserved_count or 0) - 1)
    db.commit()
    return success_response({"activity_id": activity_id, "status": "CANCELLED"}, message="预约已取消")


@router.post("/{activity_id}/attend")
def attend_activity(
    activity_id: int,
    req: AttendRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    activity = db.query(Activity).filter(Activity.id == activity_id).with_for_update().first()
    if not activity:
        return error_response(code=4040, message="活动不存在")
    now = datetime.utcnow()
    if (activity.status not in ("PUBLISHED", "ONGOING")
            or now < activity.start_at - timedelta(minutes=30) or now > activity.end_at):
        return error_response(code=4090, message="当前不在活动签到时间内")
    if not activity.checkin_code_hash or not verify_password(req.code, activity.checkin_code_hash):
        return error_response(code=4030, message="签到码不正确")
    existing = db.query(ActivityAttendance).filter(
        ActivityAttendance.activity_id == activity_id,
        ActivityAttendance.user_id == user_id
    ).first()
    if existing:
        return success_response({"activity_id": activity_id, "status": "ATTENDED", "energy_added": 0}, message="已完成签到")
    reservation = db.query(ActivityReservation).filter(
        ActivityReservation.activity_id == activity_id,
        ActivityReservation.user_id == user_id,
        ActivityReservation.status == "CONFIRMED"
    ).first()
    if not reservation:
        return error_response(code=4030, message="请先预约活动")
    db.add(ActivityAttendance(activity_id=activity_id, user_id=user_id, checked_at=now))
    reservation.status = "ATTENDED"

    event_ref = f"activity_{activity_id}"
    rewarded = db.query(GrowthEvent).filter(
        GrowthEvent.user_id == user_id,
        GrowthEvent.event_type == "CHECKIN",
        GrowthEvent.ref_id == event_ref
    ).first()
    energy_added = 0
    if not rewarded:
        energy_added = activity.energy_reward or 0
        db.add(GrowthEvent(
            user_id=user_id, event_type="CHECKIN", ref_id=event_ref, value=energy_added
        ))
        growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).with_for_update().first()
        if growth:
            growth.energy_value += energy_added
            if growth.energy_value >= 1000:
                growth.level_code = "LV3_CRAFTSMAN"
            elif growth.energy_value >= 500:
                growth.level_code = "LV2_JOURNEYMAN"
    badge_unlocked = None
    if activity.badge_id:
        badge = db.query(Badge).filter(Badge.id == activity.badge_id).first()
        user_badge = db.query(UserBadge).filter(
            UserBadge.user_id == user_id, UserBadge.badge_id == activity.badge_id
        ).first()
        if badge and not user_badge:
            db.add(UserBadge(user_id=user_id, badge_id=badge.id))
            badge_unlocked = badge.name
    db.commit()
    return success_response({
        "activity_id": activity_id,
        "status": "ATTENDED",
        "energy_added": energy_added,
        "badge_unlocked": badge_unlocked
    }, message="活动签到成功")

@router.post("/checkin")
def checkin_landmark(
    req: CheckinRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return error_response(code=4100, message="地标打卡已停用，请预约活动后使用现场签到")
