from datetime import timezone, datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Literal

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional, require_admin
from app.schemas.common import success_response
from app.models.entities import CommunityPost, SysUser, FundRecord, ActivityCheckin, HeritageLandmark, UserGrowth, SysConfig, OrderMain, OrderItem, Product, GrowthEvent
from app.models.mobile import ExchangeItem, EnergyExchange
from app.api.activity import recorded_geofence_status

router = APIRouter(prefix="/mobile", tags=["文创市集与研学数据"])


@router.get("/market/summary")
def summary(user: dict | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    total = int(db.query(func.coalesce(func.sum(FundRecord.amount_cents), 0)).scalar())
    target = db.query(SysConfig).filter_by(config_key="fund_goal_cents").first()
    try:
        goal = max(0, int(target.config_value)) if target else None
    except (ValueError, TypeError):
        goal = None
    return success_response({"creative_works": db.query(CommunityPost).filter_by(status="APPROVED").count(),
                             "creator_count": db.query(CommunityPost.user_id).filter_by(status="APPROVED").distinct().count(),
                             "student_count": db.query(SysUser).filter_by(role_code="STUDENT", status="ACTIVE").count(),
                             "fund_total_yuan": total / 100, "fund_goal_yuan": goal / 100 if goal else None,
                             "data_source": "database"})


@router.get("/me/footprints")
def footprints(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ActivityCheckin, HeritageLandmark).join(HeritageLandmark, HeritageLandmark.id == ActivityCheckin.landmark_id).filter(
        ActivityCheckin.user_id == user["user_id"]).order_by(ActivityCheckin.checked_at.desc()).all()
    growth = db.get(UserGrowth, user["user_id"])
    agri_orders = db.query(OrderMain.id).join(OrderItem, OrderItem.order_id == OrderMain.id).join(Product, Product.id == OrderItem.product_id).filter(
        OrderMain.user_id == user["user_id"], Product.category == "AGRI_PRODUCT")
    orders = agri_orders.distinct().count()
    paid_orders = agri_orders.filter(OrderMain.status.in_(["PAID", "SHIPPED", "COMPLETED"])).distinct().count()
    visited = {r.landmark_id for r, _ in rows}
    onsite = {r.landmark_id for r, l in rows if recorded_geofence_status(r, l) == "ONSITE"}
    active_ids = {row.id for row in db.query(HeritageLandmark).filter_by(status="ACTIVE").all()}
    # These are progress milestones, separate from the awarded badge catalog.
    # Unpaid/cancelled orders and cloud visits must not imply on-site completion.
    milestone_rules = [
        ("FIRST_VISIT", "初识非遗", "探访任意一处非遗基地，云端探访也可记录。", len(visited), 1),
        ("FIRST_ONSITE", "寻访匠人", "在任意一处非遗基地范围内完成现场打卡。", len(onsite), 1),
        ("FIRST_AGRI_PURCHASE", "品味乡土", "完成一笔农产订单的付款；待支付和已取消订单不计入。", paid_orders, 1),
        ("ALL_ACTIVE_ONSITE", "非遗达人", "在当前全部开放基地完成现场打卡。", len(onsite & active_ids), len(active_ids)),
    ]
    milestones = [{"code": code, "name": name, "description": description, "current": current,
                   "target": target, "completed": target > 0 and current >= target}
                  for code, name, description, current, target in milestone_rules]
    return success_response({"landmark_count": len(visited), "agri_order_count": orders, "paid_agri_order_count": paid_orders,
                             "milestones": milestones,
                             "today_landmark_count": len({r.landmark_id for r, _ in rows if r.checked_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).date() == datetime.now(ZoneInfo("Asia/Shanghai")).date()}),
                             "energy_value": growth.energy_value if growth else 0,
                             "list": [{"id": r.id, "landmark_id": l.id, "name": l.name, "cover_url": l.cover_url,
                                       "district": l.district, "in_geofence": recorded_geofence_status(r, l) == "ONSITE",
                                       "geofence_status": recorded_geofence_status(r, l),
                                       "accuracy_meters": float(r.location_accuracy_meters) if r.location_accuracy_meters is not None else None,
                                       "checked_at": r.checked_at.isoformat()} for r, l in rows]})


@router.get("/market/exchange-items")
def exchange_items(db: Session = Depends(get_db)):
    return success_response([{"id": i.id, "name": i.name, "cover_url": i.cover_url,
                              "energy_cost": i.energy_cost, "stock": i.stock}
                             for i in db.query(ExchangeItem).filter_by(status="ACTIVE").order_by(ExchangeItem.id).all()])


class ExchangeInput(BaseModel):
    request_id: str = Field(min_length=8, max_length=64)
    item_id: int = Field(gt=0)
    receiver_name: str = Field(min_length=1, max_length=64)
    receiver_phone: str = Field(min_length=5, max_length=32)
    receiver_address: str = Field(min_length=1, max_length=255)


@router.post("/market/exchanges")
def exchange(req: ExchangeInput, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SysUser).filter_by(id=user["user_id"]).with_for_update().one()
    previous = db.query(EnergyExchange).filter_by(request_id=req.request_id).first()
    if previous:
        if previous.user_id != user["user_id"]:
            raise HTTPException(409, "兑换请求标识已被使用")
        if previous.item_id != req.item_id:
            raise HTTPException(409, "兑换请求标识不能用于不同商品")
        return success_response({"id": previous.id, "status": previous.status, "energy_cost": previous.energy_cost})
    item = db.query(ExchangeItem).filter_by(id=req.item_id, status="ACTIVE").with_for_update().first()
    growth = db.get(UserGrowth, user["user_id"])
    if not item:
        raise HTTPException(404, "兑换商品不存在")
    if item.stock < 1:
        raise HTTPException(409, "兑换商品暂时缺货")
    if item.energy_cost <= 0 or not growth or growth.energy_value < item.energy_cost:
        raise HTTPException(409, "能量不足，继续学习和创作来积累能量吧")
    growth.energy_value -= item.energy_cost
    item.stock -= 1
    record = EnergyExchange(user_id=user["user_id"], item_name=item.name, energy_cost=item.energy_cost, **req.model_dump())
    db.add(record)
    db.add(GrowthEvent(user_id=user["user_id"], event_type="ENERGY_EXCHANGE", ref_id=req.request_id, value=-item.energy_cost))
    db.commit()
    return success_response({"id": record.id, "status": record.status, "energy_cost": record.energy_cost,
                             "energy_value": growth.energy_value}, message="兑换申请已提交，等待平台安排发放")


@router.get("/me/exchanges")
def my_exchanges(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return success_response([{"id": e.id, "item_name": e.item_name, "energy_cost": e.energy_cost,
                              "status": e.status, "tracking_no": e.tracking_no, "handling_note": e.handling_note,
                              "handled_at": e.handled_at.isoformat() if e.handled_at else None,
                              "created_at": e.created_at.isoformat()}
                             for e in db.query(EnergyExchange).filter_by(user_id=user["user_id"]).order_by(EnergyExchange.created_at.desc()).all()])


@router.get("/admin/exchanges")
def admin_exchanges(status: Literal["REQUESTED", "FULFILLED", "CANCELLED"] | None = None,
                    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                    user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    query = db.query(EnergyExchange)
    if status:
        query = query.filter_by(status=status)
    total = query.count()
    records = query.order_by(EnergyExchange.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success_response({"items": [{"id": e.id, "user_id": e.user_id,
                              "item_name": e.item_name, "energy_cost": e.energy_cost,
                              "status": e.status, "receiver_name": e.receiver_name, "receiver_phone": e.receiver_phone,
                              "receiver_address": e.receiver_address, "tracking_no": e.tracking_no,
                              "handling_note": e.handling_note, "handled_by": e.handled_by,
                              "handled_at": e.handled_at.isoformat() if e.handled_at else None,
                              "created_at": e.created_at.isoformat()} for e in records],
                             "total": total, "page": page, "page_size": page_size})


class ExchangeAction(BaseModel):
    status: Literal["FULFILLED", "CANCELLED"]
    tracking_no: str = Field("", max_length=128)
    handling_note: str = Field("", max_length=500)


@router.put("/admin/exchanges/{exchange_id}")
def exchange_action(exchange_id: int, req: ExchangeAction, user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    tracking, note = req.tracking_no.strip(), req.handling_note.strip()
    if req.status == "FULFILLED" and not tracking:
        raise HTTPException(422, "请填写发放凭据或物流单号")
    if req.status == "CANCELLED" and tracking:
        raise HTTPException(422, "取消兑换不能填写发放单号")
    record = db.get(EnergyExchange, exchange_id)
    if not record:
        raise HTTPException(404, "兑换申请不存在")
    db.query(SysUser).filter_by(id=record.user_id).with_for_update().one()
    record = db.query(EnergyExchange).filter_by(id=exchange_id).with_for_update().populate_existing().one()
    if record.status == req.status:
        if (record.tracking_no or "") != tracking or (record.handling_note or "") != note:
            raise HTTPException(409, "该兑换申请已处理，请刷新列表查看结果")
        return success_response({"status": record.status})
    if record.status != "REQUESTED":
        raise HTTPException(409, "该兑换申请已处理")
    if req.status == "CANCELLED":
        growth = db.query(UserGrowth).filter_by(user_id=record.user_id).with_for_update().one()
        item = db.query(ExchangeItem).filter_by(id=record.item_id).with_for_update().one()
        growth.energy_value += record.energy_cost; item.stock += 1
        db.add(GrowthEvent(user_id=record.user_id, event_type="EXCHANGE_REFUND", ref_id=str(record.id), value=record.energy_cost))
    record.status, record.tracking_no, record.handling_note = req.status, tracking, note
    record.handled_by, record.handled_at = user["user_id"], datetime.utcnow()
    db.commit()
    return success_response({"status": record.status})
