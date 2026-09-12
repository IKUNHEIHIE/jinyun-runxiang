import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.common import success_response, error_response
from app.models.entities import (
    HeritageLandmark, Activity, ActivityReservation, ActivityCheckin,
    GrowthEvent, UserGrowth, Badge, UserBadge
)

router = APIRouter(prefix="/activities", tags=["非遗活动与文旅地图"])

class CheckinRequest(BaseModel):
    landmark_id: int
    activity_id: Optional[int] = None
    latitude: float
    longitude: float

def haversine_distance(lat1, lon1, lat2, lon2):
    # 计算两个经纬度之间的地面距离(米)
    R = 6371000 # 地球半径(米)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return int(R * c)

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
    query = db.query(Activity).filter(Activity.status == "PUBLISHED")
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

@router.post("/{activity_id}/reserve")
def reserve_activity(
    activity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return error_response(code=4040, message="活动不存在")
    
    if activity.reserved_count >= activity.capacity:
        return error_response(code=4090, message="该活动预约名额已满")
    
    existing = db.query(ActivityReservation).filter(
        ActivityReservation.activity_id == activity_id,
        ActivityReservation.user_id == user_id
    ).first()
    if existing:
        return error_response(code=4090, message="您已成功预约过该活动，请勿重复预约")
    
    reservation = ActivityReservation(
        activity_id=activity_id,
        user_id=user_id,
        status="CONFIRMED"
    )
    db.add(reservation)
    activity.reserved_count += 1
    db.commit()

    return success_response({"activity_id": activity_id, "status": "CONFIRMED"}, message="预约成功")

@router.post("/checkin")
def checkin_landmark(
    req: CheckinRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    landmark = db.query(HeritageLandmark).filter(HeritageLandmark.id == req.landmark_id).first()
    if not landmark:
        return error_response(code=4040, message="地标不存在")
    
    # 计算距离
    dist = haversine_distance(req.latitude, req.longitude, float(landmark.latitude), float(landmark.longitude))
    # 研学判定：支持乡村研学现场围栏打卡与全域文化遗址云端探访打卡
    in_geofence = dist <= landmark.geofence_radius_meters

    checkin = ActivityCheckin(
        activity_id=req.activity_id,
        landmark_id=req.landmark_id,
        user_id=user_id,
        latitude=req.latitude,
        longitude=req.longitude,
        distance_meters=dist
    )
    db.add(checkin)

    # 发放能量奖励与打卡徽章
    event_ref = f"checkin_lm_{req.landmark_id}"
    exist_ev = db.query(GrowthEvent).filter(
        GrowthEvent.user_id == user_id,
        GrowthEvent.event_type == "CHECKIN",
        GrowthEvent.ref_id == event_ref
    ).first()

    energy_added = 0
    if not exist_ev:
        energy_added = 30
        db.add(GrowthEvent(
            user_id=user_id,
            event_type="CHECKIN",
            ref_id=event_ref,
            value=energy_added
        ))
        growth = db.query(UserGrowth).filter(UserGrowth.user_id == user_id).first()
        if growth:
            growth.energy_value += energy_added
        
        # 激活徽章 #4 (乡村美育使者)
        exist_b = db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == 4).first()
        if not exist_b:
            db.add(UserBadge(user_id=user_id, badge_id=4))

    db.commit()

    return success_response({
        "landmark_name": landmark.name,
        "distance_meters": dist,
        "in_geofence": in_geofence,
        "energy_added": energy_added,
        "badge_unlocked": "乡村美育使者" if not exist_ev else None
    }, message=f"打卡成功！您已打卡【{landmark.name}】")
