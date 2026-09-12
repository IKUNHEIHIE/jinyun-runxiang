import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.common import success_response, error_response
from app.models.entities import Product, ProductSku, OrderMain, FundRecord

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

    res = []
    for p in products:
        skus = db.query(ProductSku).filter(ProductSku.product_id == p.id).all()
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

    for item in req.items:
        sku = db.query(ProductSku).filter(ProductSku.id == item.sku_id).first()
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not sku or not prod:
            return error_response(code=4040, message="商品SKU不存在")
        if sku.stock < item.quantity:
            return error_response(code=4090, message=f"商品【{sku.name}】库存不足")
        
        sku.stock -= item.quantity
        line_total = sku.price_cents * item.quantity
        total_cents += line_total
        total_fund_cents += int(line_total * float(prod.fund_rate_percent) / 100.0)

    order = OrderMain(
        order_no=order_no,
        user_id=user_id,
        total_amount_cents=total_cents,
        fund_amount_cents=total_fund_cents,
        status="PAID",  # 开发直接模拟支付完成
        receiver_name=req.receiver_name,
        receiver_phone=req.receiver_phone,
        receiver_address=req.receiver_address,
        pay_time=datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 注入专项基金流水
    fund_rec = FundRecord(
        source_order_id=order.id,
        amount_cents=total_fund_cents,
        purpose="乡村小学非遗美育耗材定向采购",
        status="ALLOCATED"
    )
    db.add(fund_rec)
    db.commit()

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
