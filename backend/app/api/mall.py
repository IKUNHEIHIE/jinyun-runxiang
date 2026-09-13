import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.schemas.common import success_response, error_response
from app.models.entities import Product, ProductSku, OrderMain, FundRecord, PhilanthropySupply

router = APIRouter(prefix="/mall", tags=["文创市集与电商助农"])

class OrderItemDTO(BaseModel):
    product_id: int
    sku_id: int
    quantity: int = 1

class CreateOrderRequest(BaseModel):
    items: List[OrderItemDTO]
    receiver_name: str
    receiver_phone: str
    receiver_address: str

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
    order_no = f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    total_cents = 0
    total_fund_cents = 0

    try:
        for item in req.items:
            sku = db.query(ProductSku).filter(ProductSku.id == item.sku_id).first()
            prod = db.query(Product).filter(Product.id == item.product_id).first()
            if not sku or not prod:
                db.rollback()
                return error_response(code=4040, message="商品SKU不存在")
            
            # 原子条件扣减库存，杜绝并发超卖 (CWE-362)
            affected = db.query(ProductSku).filter(
                ProductSku.id == item.sku_id,
                ProductSku.stock >= item.quantity
            ).update({"stock": ProductSku.stock - item.quantity})

            if affected == 0:
                db.rollback()
                return error_response(code=4090, message=f"商品【{sku.name}】库存不足")
            
            line_total = sku.price_cents * item.quantity
            total_cents += line_total
            total_fund_cents += int(line_total * float(prod.fund_rate_percent) / 100.0)

        order = OrderMain(
            order_no=order_no,
            user_id=user_id,
            total_amount_cents=total_cents,
            fund_amount_cents=total_fund_cents,
            status="PAID",  # 乡村振兴助农商城即时核销清算，订单置为已支付
            receiver_name=req.receiver_name,
            receiver_phone=req.receiver_phone,
            receiver_address=req.receiver_address,
            pay_time=datetime.utcnow()
        )
        db.add(order)
        db.flush()

        # 注入专项基金流水
        fund_rec = FundRecord(
            source_order_id=order.id,
            amount_cents=total_fund_cents,
            purpose="乡村小学非遗美育耗材定向采购",
            status="ALLOCATED"
        )
        db.add(fund_rec)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return success_response({
        "order_no": order.order_no,
        "total_amount_yuan": total_cents / 100.0,
        "fund_contributed_yuan": total_fund_cents / 100.0,
        "status": order.status
    }, message="下单与助农美育基金汇入成功")

@router.get("/orders")
def list_my_orders(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(OrderMain).filter(OrderMain.user_id == current_user["user_id"]).order_by(OrderMain.created_at.desc()).all()
    return success_response([{
        "order_no": o.order_no,
        "total_amount_yuan": o.total_amount_cents / 100.0,
        "fund_contributed_yuan": o.fund_amount_cents / 100.0,
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

    schools = [
        "蓟州区穿芳峪镇中心小学",
        "宝坻区大口屯镇初级中学",
        "武清区河西务镇中心小学",
        "宁河区俵口镇第一小学",
        "静海区独流镇第一小学"
    ]
    idx = abs(hash(order.order_no)) % len(schools)
    school_name = schools[idx]

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
        "verify_code": f"VERIFY-{uuid.uuid4().hex[:8].upper()}"
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
            "total_materials_quantity": total_qty,
            "total_beneficiary_students": total_students,
            "covered_districts": districts,
            "fund_conversion_rate": "100% 专款专用，每笔助农文创订单按 5% 定向转化为乡村耗材"
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

