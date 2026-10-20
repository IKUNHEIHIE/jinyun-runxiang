"""Daily quota and short-window throttling for AI workshop generation endpoints."""
import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import AiTask, SysConfig

SHANGHAI = timezone(timedelta(hours=8))
DEFAULTS = {
    "daily_total": 60,
    "daily_silhouette": 50,
    "daily_mesh_3d": 50,
    "per_minute": 30,
}
# Tool families that share the daily total; SILHOUETTE and MESH_3D have their own counters too.
COUNTED_TOOLS = ("SHADOW_PUPPET", "BRONZE", "BALLAD", "LACQUER", "EMBROIDERY", "MESH_3D", "SILHOUETTE")


def limits(db: Session) -> Dict[str, int]:
    row = db.query(SysConfig).filter(SysConfig.config_key == "ai_quota").first()
    configured = {}
    if row and row.config_value:
        try:
            loaded = json.loads(row.config_value)
            configured = {k: int(v) for k, v in loaded.items() if isinstance(v, (int, str)) and str(v).isdigit()}
        except (ValueError, AttributeError):
            configured = {}
    merged = dict(DEFAULTS)
    merged.update(configured)
    return merged


def day_start_utc() -> datetime:
    """Naive UTC boundary of the current Asia/Shanghai calendar day, matching stored timestamps."""
    now = datetime.now(SHANGHAI)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.astimezone(timezone.utc).replace(tzinfo=None)


def usage_today(db: Session, user_id: int) -> Dict[str, int]:
    tools = tuple(tool for tool in COUNTED_TOOLS)
    rows = (db.query(AiTask.tool_type).filter(AiTask.user_id == user_id, AiTask.created_at >= day_start_utc(),
                                              AiTask.tool_type.in_(tools)).all())
    used = defaultdict(int)
    for (tool,) in rows:
        used[tool] += 1
    total = sum(used.values())
    cfg = limits(db)
    return {
        "total": total,
        "silhouette": used["SILHOUETTE"],
        "mesh_3d": used["MESH_3D"],
        "remaining_total": max(0, cfg["daily_total"] - total),
        "remaining_silhouette": max(0, cfg["daily_silhouette"] - used["SILHOUETTE"]),
        "remaining_mesh_3d": max(0, cfg["daily_mesh_3d"] - used["MESH_3D"]),
        "limits": cfg,
    }


def enforce_daily(db: Session, user_id: int, bucket: str) -> Dict[str, int]:
    cfg = limits(db)
    usage = usage_today(db, user_id)
    cap = {"silhouette": cfg["daily_silhouette"], "mesh_3d": cfg["daily_mesh_3d"], "total": cfg["daily_total"]}[bucket]
    used = usage[bucket]
    if used >= cap:
        label = {"silhouette": "剪影生成", "mesh_3d": "三维生成", "total": "今日创作"}[bucket]
        raise HTTPException(429, f"{label}今日次数已用完（{cap} 次），请明天再试或联系老师调整额度")
    return usage


_windows: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def throttle(user_id: int, route: str, per_minute: int) -> None:
    """Single-process guard against scripted bursts; the daily quota is the durable limit."""
    key = f"{user_id}:{route}"
    now = time.monotonic()
    with _lock:
        window = _windows[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= per_minute:
            raise HTTPException(429, "操作过于频繁，请稍后再试")
        window.append(now)


def reset_windows() -> None:
    with _lock:
        _windows.clear()
