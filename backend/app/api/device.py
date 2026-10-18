from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import require_teacher
from app.schemas.common import success_response, error_response
from app.models.entities import Device

router = APIRouter(prefix="/devices", tags=["具身智能与设备网关"])

class DeviceCommandRequest(BaseModel):
    command_type: str  # PERFORM_SHADOW_PLAY, SPEAK_EXPLANATION, RESET
    payload: Dict[str, Any]

@router.get("")
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    return success_response([{
        "id": d.id,
        "device_code": d.device_code,
        "device_name": d.device_name,
        "model": d.model,
        "firmware_version": d.firmware_version,
        "status": d.status,
        "last_seen_at": d.last_seen_at.strftime("%Y-%m-%d %H:%M:%S") if d.last_seen_at else "",
        "telemetry": {
            "battery_pct": None,
            "wifi_rssi": None,
            "cpu_temp_c": None
        }
    } for d in devices])

@router.get("/{device_code}/status")
def get_device_status(device_code: str, db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.device_code == device_code).first()
    if not d:
        return error_response(code=4040, message="设备不存在")
    return success_response({
        "device_code": d.device_code,
        "name": d.device_name,
        "status": d.status,
        "is_online": d.status == "ONLINE",
        "battery": None,
        "current_task": None,
        "fallback_available": True
    })

@router.post("/{device_code}/command")
def send_device_command(
    device_code: str,
    req: DeviceCommandRequest,
    current_user: dict = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    d = db.query(Device).filter(Device.device_code == device_code).first()
    if not d:
        return error_response(code=4040, message="设备不存在")

    raise HTTPException(503, "设备网关尚未接入，未发送指令")
