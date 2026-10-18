from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import success_response
from app.models.entities import SysUser, UserProfile, CommunityPost, OrderMain, FundRecord, Device, AiTask
from datetime import datetime

router = APIRouter(prefix="/screen", tags=["乡村美育数字化大屏数据中台"])

@router.get("/overview")
def get_screen_overview(db: Session = Depends(get_db)):
    students = db.query(SysUser).filter(SysUser.role_code == "STUDENT").count()
    schools = db.query(func.count(func.distinct(UserProfile.school_name))).filter(UserProfile.school_name != "").scalar() or 0
    creations = db.query(AiTask).filter(AiTask.status == "SUCCESS").count()
    fund = db.query(func.coalesce(func.sum(FundRecord.amount_cents), 0)).scalar()
    devices = db.query(Device).all()
    kpis = [
        {"icon": "🏫", "label": "覆盖学校", "value": str(schools), "unit": "所", "subtext": "已登记学校", "color": "#00f2fe"},
        {"icon": "🎨", "label": "注册学子", "value": str(students), "unit": "人", "subtext": "实际学生账号", "color": "#4facfe"},
        {"icon": "✨", "label": "AI生成", "value": str(creations), "unit": "件", "subtext": "已完成任务", "color": "#f9d423"},
        {"icon": "🧧", "label": "公益金", "value": f"{fund / 100:.2f}", "unit": "元", "subtext": "已确认基金流水", "color": "#ff4b2b"},
        {"icon": "🤖", "label": "机器人授课", "value": "—", "unit": "课时", "subtext": "等待接入真实授课记录", "color": "#00e676"}
    ]
    categories = db.query(CommunityPost.category, func.count(CommunityPost.id)).filter(
        CommunityPost.status == "APPROVED").group_by(CommunityPost.category).all()
    districts = db.query(UserProfile.district, func.count(UserProfile.user_id)).join(
        SysUser, SysUser.id == UserProfile.user_id).filter(SysUser.role_code == "STUDENT",
        UserProfile.district.isnot(None)).group_by(UserProfile.district).all()
    aesthetic_keys = ["composition", "color", "linework", "heritage", "innovation"]
    aesthetic_values = {key: [] for key in aesthetic_keys}
    aesthetic_sample_count = 0
    for task in db.query(AiTask).filter(AiTask.status == "SUCCESS").all():
        summary = task.result_summary_json or {}
        scores = summary.get("aesthetic_scores") if isinstance(summary, dict) else None
        if not isinstance(scores, dict):
            continue
        usable = {key: scores.get(key) for key in aesthetic_keys
                  if isinstance(scores.get(key), (int, float))}
        if len(usable) != len(aesthetic_keys):
            continue
        aesthetic_sample_count += 1
        for key, value in usable.items():
            aesthetic_values[key].append(float(value))
    aesthetic_matrix = {
        "sample_count": aesthetic_sample_count,
        "scores": {
            key: round(sum(values) / len(values), 1) if values else None
            for key, values in aesthetic_values.items()
        },
    }
    orders = db.query(OrderMain).filter(OrderMain.status.in_(["PAID", "SHIPPED", "COMPLETED"])).order_by(OrderMain.created_at.desc()).limit(15).all()
    donations = []
    for order in orders:
        user = db.get(SysUser, order.user_id)
        donations.append({"time": order.created_at.strftime("%H:%M:%S"),
            "user": user.nickname[:1] + "*" if user else "爱心用户", "item": "文创订单",
            "school": "待物资调拨确认", "fund": f"{order.fund_amount_cents / 100:.2f}",
            "hash": order.order_no[-6:]})
    return success_response({"kpis": kpis,
        "pie_chart": [{"name": category, "value": count} for category, count in categories],
        "bar_chart": {"categories": [d for d, _ in districts], "values": [c for _, c in districts]},
        "aesthetic_matrix": aesthetic_matrix,
        "donation_orders": donations,
        "robots": [{"id": d.device_code, "name": d.device_name, "location": d.school_id or "未登记",
                    "task": "等待设备回执", "battery": None, "temp": None, "latency": None,
                    "statusText": {"ONLINE": "在线", "OFFLINE": "离线"}.get(d.status, d.status),
                    "statusClass": "running" if d.status == "ONLINE" else "idle", "is_twin_mode": False} for d in devices],
        "updated_at": datetime.utcnow().isoformat(), "data_source": "database"})
