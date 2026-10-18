"""运营后台目录管理：徽章、市集商品、能量兑换商品。"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.common import success_response
from app.models.entities import Badge, UserBadge, Product, ProductSku
from app.models.mobile import ExchangeItem

router = APIRouter(prefix="/admin/catalog", tags=["运营后台目录管理"])


class BadgeUpsert(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=255)
    icon_url: str = Field(min_length=1, max_length=500)
    condition_json: dict | None = None


class ProductUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    category: str = Field("CULTURAL_CREATIVE", max_length=32)
    cover_url: str = Field(min_length=1, max_length=500)
    origin_place: str | None = Field(None, max_length=128)
    story: str | None = None
    fund_rate_percent: float = Field(10, ge=0, le=100)
    status: str = Field("ON_SALE", pattern="^(ON_SALE|OFF_SALE)$")
    sku_name: str | None = Field(None, max_length=128)
    price_cents: int = Field(0, ge=0)
    stock: int = Field(0, ge=0)


class ExchangeItemUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    cover_url: str | None = Field(None, max_length=500)
    energy_cost: int = Field(..., gt=0, le=1000000)
    stock: int = Field(0, ge=0)
    status: str = Field("ACTIVE", pattern="^(ACTIVE|INACTIVE)$")


def _badge_payload(row: Badge) -> dict:
    return {
        "id": row.id, "code": row.code, "name": row.name,
        "description": row.description, "icon_url": row.icon_url,
        "condition_json": row.condition_json,
    }


def _product_payload(db: Session, row: Product) -> dict:
    sku = db.query(ProductSku).filter_by(product_id=row.id).order_by(ProductSku.id).first()
    return {
        "id": row.id, "name": row.name, "category": row.category,
        "cover_url": row.cover_url, "origin_place": row.origin_place,
        "story": row.story, "fund_rate_percent": float(row.fund_rate_percent or 0),
        "status": row.status,
        "sku_id": sku.id if sku else None,
        "sku_name": sku.name if sku else "",
        "price_cents": sku.price_cents if sku else None,
        "stock": sku.stock if sku else None,
    }


def _exchange_payload(row: ExchangeItem) -> dict:
    return {
        "id": row.id, "name": row.name, "cover_url": row.cover_url,
        "energy_cost": row.energy_cost, "stock": row.stock, "status": row.status,
    }


@router.get("/badges")
def list_badge_catalog(current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Badge).order_by(Badge.id).all()
    counts = {
        badge_id: db.query(UserBadge).filter_by(badge_id=badge_id).count()
        for badge_id in [row.id for row in rows]
    }
    return success_response([
        _badge_payload(row) | {"holders": counts.get(row.id, 0)} for row in rows
    ])


@router.post("/badges")
def create_badge(req: BadgeUpsert, current_user: dict = Depends(require_admin),
                 db: Session = Depends(get_db)):
    if db.query(Badge).filter_by(code=req.code.strip().upper()).first():
        raise HTTPException(409, "徽章代码已存在")
    row = Badge(code=req.code.strip().upper(), name=req.name.strip(),
                description=req.description.strip(), icon_url=req.icon_url.strip(),
                condition_json=req.condition_json)
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(_badge_payload(row), message="徽章已创建")


@router.put("/badges/{badge_id}")
def update_badge(badge_id: int, req: BadgeUpsert,
                 current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(Badge, badge_id)
    if not row:
        raise HTTPException(404, "徽章不存在")
    if db.query(Badge).filter(Badge.code == req.code.strip().upper(), Badge.id != badge_id).first():
        raise HTTPException(409, "徽章代码已存在")
    row.code = req.code.strip().upper()
    row.name = req.name.strip()
    row.description = req.description.strip()
    row.icon_url = req.icon_url.strip()
    row.condition_json = req.condition_json
    db.commit()
    db.refresh(row)
    return success_response(_badge_payload(row), message="徽章已更新")


@router.delete("/badges/{badge_id}")
def delete_badge(badge_id: int, current_user: dict = Depends(require_admin),
                 db: Session = Depends(get_db)):
    row = db.get(Badge, badge_id)
    if not row:
        raise HTTPException(404, "徽章不存在")
    if db.query(UserBadge).filter_by(badge_id=badge_id).first():
        raise HTTPException(409, "已有用户获得该徽章，不能删除；请调整名称或图标")
    db.delete(row)
    db.commit()
    return success_response({"id": badge_id}, message="徽章已删除")


@router.get("/products")
def list_product_catalog(current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Product).order_by(Product.id).all()
    return success_response([_product_payload(db, row) for row in rows])


@router.post("/products")
def create_product(req: ProductUpsert, current_user: dict = Depends(require_admin),
                   db: Session = Depends(get_db)):
    row = Product(name=req.name.strip(), category=req.category, cover_url=req.cover_url.strip(),
                  origin_place=req.origin_place, story=req.story,
                  fund_rate_percent=req.fund_rate_percent, status=req.status)
    db.add(row)
    db.flush()
    db.add(ProductSku(product_id=row.id, sku_code="SKU-" + uuid.uuid4().hex[:10].upper(),
                      name=(req.sku_name or req.name).strip(),
                      price_cents=req.price_cents, stock=req.stock))
    db.commit()
    db.refresh(row)
    return success_response(_product_payload(db, row), message="商品已创建")


@router.put("/products/{product_id}")
def update_product(product_id: int, req: ProductUpsert,
                   current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(Product, product_id)
    if not row:
        raise HTTPException(404, "商品不存在")
    row.name = req.name.strip()
    row.category = req.category
    row.cover_url = req.cover_url.strip()
    row.origin_place = req.origin_place
    row.story = req.story
    row.fund_rate_percent = req.fund_rate_percent
    row.status = req.status
    sku = db.query(ProductSku).filter_by(product_id=row.id).order_by(ProductSku.id).first()
    if not sku:
        db.add(ProductSku(product_id=row.id, sku_code="SKU-" + uuid.uuid4().hex[:10].upper(),
                          name=(req.sku_name or req.name).strip(),
                          price_cents=req.price_cents, stock=req.stock))
    else:
        sku.name = (req.sku_name or req.name).strip()
        sku.price_cents = req.price_cents
        sku.stock = req.stock
    db.commit()
    db.refresh(row)
    return success_response(_product_payload(db, row), message="商品已更新")


@router.get("/exchange-items")
def list_exchange_catalog(current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(ExchangeItem).order_by(ExchangeItem.id).all()
    return success_response([_exchange_payload(row) for row in rows])


@router.post("/exchange-items")
def create_exchange_item(req: ExchangeItemUpsert,
                         current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    row = ExchangeItem(name=req.name.strip(), cover_url=req.cover_url,
                       energy_cost=req.energy_cost, stock=req.stock, status=req.status)
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(_exchange_payload(row), message="兑换商品已创建")


@router.put("/exchange-items/{item_id}")
def update_exchange_item(item_id: int, req: ExchangeItemUpsert,
                         current_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(ExchangeItem, item_id)
    if not row:
        raise HTTPException(404, "兑换商品不存在")
    row.name = req.name.strip()
    row.cover_url = req.cover_url
    row.energy_cost = req.energy_cost
    row.stock = req.stock
    row.status = req.status
    db.commit()
    db.refresh(row)
    return success_response(_exchange_payload(row), message="兑换商品已更新")
