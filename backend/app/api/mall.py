import uuid
import hashlib
import hmac
from decimal import Decimal, ROUND_DOWN
from app.core.config import settings
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.common import success_response, error_response
from app.models.entities import Product, ProductSku, OrderMain, FundRecord, PhilanthropySupply, OrderItem, SysUser

router = APIRouter(prefix="/mall", tags=["文创市集与电商助农"])

class OrderItemDTO(BaseModel):
    product_id: int
    sku_id: int
    quantity: int = Field(1, ge=1, le=100)

class CreateOrderRequest(BaseModel):
    request_id: Optional[str] = Field(None, min_length=8, max_length=64)
    items: List[OrderItemDTO] = Field(..., min_length=1, max_length=50)
    receiver_name: str = Field(..., min_length=1, max_length=64)
    receiver_phone: str = Field(..., min_length=5, max_length=32)
    receiver_address: str = Field(..., min_length=1, max_length=255)

@router.get("/products")
def list_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.status == "ON_SALE")
    if category:
        query = query.filter(Product.category == category)
    products = query.all()
    if not products:
        return success_response([])

    # 性能优化：批量 in_ 加载消除 N+1 数据库并发查询
    product_ids = [p.id for p in products]
    all_skus = db.query(ProductSku).filter(ProductSku.product_id.in_(product_ids)).all()
    skus_by_prod = {}
    for sku in all_skus:
        skus_by_prod.setdefault(sku.product_id, []).append(sku)

    res = []
    for p in products:
        skus = skus_by_prod.get(p.id, [])
        min_price = min([s.price_cents for s in skus]) if skus else 0
        res.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "cover_url": p.cover_url,
            "origin_place": p.origin_place,
            "story": p.story,
            "fund_rate_percent": float(p.fund_rate_percent),
            "starting_price_yuan": min_price / 100.0,
            "skus": [{
                "id": s.id,
                "name": s.name,
                "price_cents": s.price_cents,
                "price_yuan": s.price_cents / 100.0,
                "stock": s.stock
            } for s in skus]
        })
    return success_response(res)

@router.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return error_response(code=4040, message="商品不存在")
    skus = db.query(ProductSku).filter(ProductSku.product_id == p.id).all()
    return success_response({
        "id": p.id,
        "name": p.name,
        "category": p.category,
        "cover_url": p.cover_url,
        "origin_place": p.origin_place,
        "story": p.story,
        "fund_rate_percent": float(p.fund_rate_percent),
        "skus": [{
            "id": s.id,
            "name": s.name,
            "price_cents": s.price_cents,
            "price_yuan": s.price_cents / 100.0,
            "stock": s.stock
        } for s in skus]
    })

@router.post("/orders")
def create_order(
    req: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    if req.request_id:
        db.query(SysUser).filter(SysUser.id == user_id).with_for_update().one()
        previous = db.query(OrderMain).filter_by(client_request_id=req.request_id).first()
        if previous:
            if previous.user_id != user_id:
                raise HTTPException(409, "订单请求标识已被使用")
            lines = db.query(OrderItem).filter_by(order_id=previous.id).all()
            old_items = sorted((i.product_id, i.sku_id, i.quantity) for i in lines)
            new_items = sorted((i.product_id, i.sku_id, i.quantity) for i in req.items)
            if old_items != new_items or any(getattr(previous, k) != getattr(req, k)
                                            for k in ("receiver_name", "receiver_phone", "receiver_address")):
                raise HTTPException(409, "订单请求标识不能用于不同订单")
            return success_response({"order_no": previous.order_no, "total_amount_yuan": previous.total_amount_cents / 100,
                                     "fund_contributed_yuan": previous.fund_amount_cents / 100 if previous.status in {"PAID", "SHIPPED", "COMPLETED"} else 0,
                                     "status": previous.status})
    order_no = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    total_cents = 0
    total_fund_cents = 0
    snapshots = []
    if len({item.sku_id for item in req.items}) != len(req.items):
        raise HTTPException(422, "商品规格不可重复，请合并购买数量")
    try:
        for item in sorted(req.items, key=lambda item: item.sku_id):
            prod = db.query(Product).filter(Product.id == item.product_id,
                                            Product.status == "ON_SALE").with_for_update().first()
            sku = db.query(ProductSku).filter(ProductSku.id == item.sku_id,
                                              ProductSku.product_id == item.product_id).first()
            if not sku or not prod:
                raise HTTPException(404, "在售商品或商品规格不存在")
            rate = Decimal(prod.fund_rate_percent)
            if sku.price_cents <= 0 or not Decimal(0) <= rate <= Decimal(100):
                raise HTTPException(409, "商品价格或公益比例无效")
            affected = db.query(ProductSku).filter(
                ProductSku.id == item.sku_id, ProductSku.stock >= item.quantity
            ).update({"stock": ProductSku.stock - item.quantity}, synchronize_session=False)
            if affected != 1:
                raise HTTPException(409, "商品库存不足")
            line_total = sku.price_cents * item.quantity
            total_cents += line_total
            total_fund_cents += int((Decimal(line_total) * rate / 100).to_integral_value(rounding=ROUND_DOWN))
            if total_cents > 2_000_000_000:
                raise HTTPException(422, "订单金额超过限制")
            snapshots.append(dict(product_id=prod.id, sku_id=sku.id, product_name=prod.name,
                                  sku_name=sku.name, price_cents=sku.price_cents, quantity=item.quantity))
        order = OrderMain(order_no=order_no, user_id=user_id, total_amount_cents=total_cents,
                          client_request_id=req.request_id,
                          fund_amount_cents=total_fund_cents, status="CREATED",
                          receiver_name=req.receiver_name, receiver_phone=req.receiver_phone,
                          receiver_address=req.receiver_address, pay_time=None)
        db.add(order)
        db.flush()
        db.add_all([OrderItem(order_id=order.id, **item) for item in snapshots])
        db.commit()
    except Exception:
        db.rollback()
        raise
    return success_response({"order_no": order.order_no, "total_amount_yuan": total_cents / 100,
                             "fund_contributed_yuan": 0, "status": order.status},
                            message="订单已创建，待确认付款后计入公益基金")


@router.post("/orders/{order_no}/cancel")
def cancel_order(order_no: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(OrderMain).filter(OrderMain.order_no == order_no,
                                      OrderMain.user_id == current_user["user_id"]).with_for_update().first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status == "CANCELLED":
        return success_response({"status": "CANCELLED"})
    if order.status != "CREATED":
        raise HTTPException(409, "当前订单不可取消")
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).order_by(OrderItem.sku_id).all()
    if not items:
        raise HTTPException(409, "历史订单缺少明细，请联系管理员处理")
    for item in items:
        db.query(ProductSku).filter(ProductSku.id == item.sku_id).update(
            {"stock": ProductSku.stock + item.quantity}, synchronize_session=False
        )
    order.status = "CANCELLED"
    db.commit()
    return success_response({"status": "CANCELLED"}, message="订单已取消，库存已释放")


@router.get("/orders")
def list_my_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(OrderMain).filter(OrderMain.user_id == current_user["user_id"]).order_by(OrderMain.created_at.desc()).all()
    return success_response([{
        "order_no": o.order_no,
        "total_amount_yuan": o.total_amount_cents / 100.0,
        "fund_contributed_yuan": o.fund_amount_cents / 100.0 if o.status in {"PAID", "SHIPPED", "COMPLETED"} else 0,
        "status": o.status,
        "receiver_name": o.receiver_name,
        "created_at": o.created_at.strftime("%Y-%m-%d %H:%M")
    } for o in orders])

@router.get("/orders/{order_no}/certificate")
def get_order_certificate(
    order_no: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文创助农爱心捐赠电子证书元数据"""
    order = db.query(OrderMain).filter(
        OrderMain.order_no == order_no,
        OrderMain.user_id == current_user["user_id"]
    ).first()
    if not order:
        return error_response(code=4040, message="订单不存在或无权查看")

    fund = db.query(FundRecord).filter(FundRecord.source_order_id == order.id).first()
    if order.status not in {"PAID", "SHIPPED", "COMPLETED"} or not fund:
        raise HTTPException(409, "尚未确认付款及公益入账，暂不能颁发证书")
    school_name = "受助学校待物资调拨确认"
    verify_code = hmac.new(settings.JWT_SECRET_KEY.encode(), order.order_no.encode(), hashlib.sha256).hexdigest()[:24].upper()

    return success_response({
        "certificate_no": f"JY-LOVE-{order.order_no[-8:]}",
        "order_no": order.order_no,
        "donor_name": order.receiver_name or current_user.get("nickname", "爱心助农者"),
        "total_amount_yuan": order.total_amount_cents / 100.0,
        "fund_amount_yuan": order.fund_amount_cents / 100.0,
        "beneficiary_school": school_name,
        "purpose": "天津乡村小学非遗美育耗材（皮影皮料、年画刻刀与宣纸）专项采购",
        "issue_date": order.created_at.strftime("%Y年%m月%d日"),
        "seal_title": "津韵润乡·乡村美育振兴专项认证",
        "verify_code": f"VERIFY-{verify_code}"
    })

@router.get("/philanthropy/supplies")
def list_philanthropy_supplies(db: Session = Depends(get_db)):
    """
    获取美育微光林·助农物资实体流向树数据 (已为乡村小学送出的真实物资批次明细)
    """
    supplies = db.query(PhilanthropySupply).order_by(PhilanthropySupply.delivered_date.desc()).all()
    total_qty = sum(s.quantity for s in supplies)
    total_students = sum(s.beneficiary_students for s in supplies)
    districts = list(set(s.district for s in supplies))

    return success_response({
        "summary": {
            "total_batches": len(supplies),
            "fund_total_yuan": (db.query(func.coalesce(func.sum(FundRecord.amount_cents), 0)).scalar() or 0) / 100,
            "total_materials_quantity": total_qty,
            "total_beneficiary_students": total_students,
            "covered_districts": districts,
            "fund_conversion_rate": "按各商品公示比例计算，以确认入账为准"
        },
        "supplies": [{
            "id": s.id,
            "school_name": s.school_name,
            "district": s.district,
            "materials_name": s.materials_name,
            "quantity": s.quantity,
            "unit": s.unit,
            "beneficiary_students": s.beneficiary_students,
            "delivered_date": s.delivered_date,
            "batch_no": s.batch_no,
            "photo_url": s.photo_url,
            "status": s.status
        } for s in supplies]
    })

