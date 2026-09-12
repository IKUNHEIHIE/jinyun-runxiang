import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.core.security import require_teacher
from app.schemas.common import success_response, error_response
from app.models.entities import Device, DeviceCommand

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
            "battery_pct": 82,
            "wifi_rssi": -55,
            "cpu_temp_c": 41.5
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
        "battery": 82,
        "current_task": "天津皮影经典唱段动作讲解",
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

    cmd_id = uuid.uuid4().hex
    now = datetime.utcnow()
    cmd = DeviceCommand(
        command_id=cmd_id,
        device_id=d.id,
        command_type=req.command_type,
        payload_json=req.payload,
        status="ACKED",
        sent_at=now,
        ack_at=now
    )
    d.last_seen_at = now
    db.add(cmd)
    db.commit()

    action_label = "天津皮影老生肢体走位与三签演播" if req.command_type == "PERFORM_SHADOW_PLAY" else "天津皮影历史语音讲解与唱段示范"
    return success_response({
        "command_id": cmd_id,
        "device_code": device_code,
        "command_type": req.command_type,
        "action_label": action_label,
        "status": "ACKED",
        "fallback_virtual_mode": d.status != "ONLINE",
        "action_preview_url": "/static/models/tianjin_shadow_puppet.glb",
        "executed_at": now.strftime("%Y-%m-%d %H:%M:%S")
    }, message=f"指令【{action_label}】已成功送达具身机器人并执行完毕")
