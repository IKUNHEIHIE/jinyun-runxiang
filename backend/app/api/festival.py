from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.security import require_admin, get_current_user_optional
from app.schemas.common import success_response, error_response
from app.models.entities import FolkFestival

router = APIRouter(tags=["津门民俗与岁时节日"])

class FestivalCreateRequest(BaseModel):
    title: str
    lunar_date: str
    solar_date: Optional[str] = None
    category: str = "FOLK_CUSTOM"
    tag: str = "津沽民俗专题"
    customs: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = "/static/images/painting_1.svg"
    status: str = "PUBLISHED"
    sort_order: int = 0

class FestivalUpdateRequest(BaseModel):
    title: Optional[str] = None
    lunar_date: Optional[str] = None
    solar_date: Optional[str] = None
    category: Optional[str] = None
    tag: Optional[str] = None
    customs: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None

@router.get("/festivals")
def list_festivals(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取津门民俗节日列表（前台与运营后台共用）"""
    query = db.query(FolkFestival)
    if status:
        query = query.filter(FolkFestival.status == status)
    if category:
        query = query.filter(FolkFestival.category == category)
    
    festivals = query.order_by(FolkFestival.sort_order.asc(), FolkFestival.id.asc()).all()
    
    return success_response([{
        "id": f.id,
        "title": f.title,
        "solar_date": f.solar_date,
        "lunar_date": f.lunar_date,
        "category": f.category,
        "tag": f.tag,
        "customs": f.customs,
        "description": f.description,
        "cover_url": f.cover_url,
        "status": f.status,
        "sort_order": f.sort_order,
        "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else ""
    } for f in festivals])

@router.get("/festivals/{festival_id}")
def get_festival(festival_id: int, db: Session = Depends(get_db)):
    """获取单个民俗节日详情"""
    f = db.query(FolkFestival).filter(FolkFestival.id == festival_id).first()
    if not f:
        return error_response(code=4040, message="民俗节日不存在")
    return success_response({
        "id": f.id,
        "title": f.title,
        "solar_date": f.solar_date,
        "lunar_date": f.lunar_date,
        "category": f.category,
        "tag": f.tag,
        "customs": f.customs,
        "description": f.description,
        "cover_url": f.cover_url,
        "status": f.status,
        "sort_order": f.sort_order,
        "created_at": f.created_at.strftime("%Y-%m-%d %H:%M:%S") if f.created_at else ""
    })

@router.post("/admin/festivals")
def create_festival(
    req: FestivalCreateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """运营管理后台：新增民俗节日"""
    festival = FolkFestival(
        title=req.title,
        lunar_date=req.lunar_date,
        solar_date=req.solar_date,
        category=req.category,
        tag=req.tag,
        customs=req.customs,
        description=req.description,
        cover_url=req.cover_url or "/static/images/painting_1.svg",
        status=req.status,
        sort_order=req.sort_order
    )
    db.add(festival)
    db.commit()
    db.refresh(festival)
    return success_response({
        "id": festival.id,
        "title": festival.title
    }, message=f"民俗节日【{festival.title}】发布成功")

@router.put("/admin/festivals/{festival_id}")
def update_festival(
    festival_id: int,
    req: FestivalUpdateRequest,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """运营管理后台：编辑民俗节日"""
    f = db.query(FolkFestival).filter(FolkFestival.id == festival_id).first()
    if not f:
        return error_response(code=4040, message="民俗节日不存在")

    update_fields = req.dict(exclude_unset=True)
    for k, v in update_fields.items():
        setattr(f, k, v)
    f.updated_at = datetime.utcnow()
    db.commit()
    return success_response({"id": f.id}, message="民俗节日信息已更新")

@router.put("/admin/festivals/{festival_id}/status")
def toggle_festival_status(
    festival_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """运营管理后台：上下架民俗节日"""
    f = db.query(FolkFestival).filter(FolkFestival.id == festival_id).first()
    if not f:
        return error_response(code=4040, message="民俗节日不存在")

    new_status = "OFFLINE" if f.status == "PUBLISHED" else "PUBLISHED"
    f.status = new_status
    f.updated_at = datetime.utcnow()
    db.commit()
    action_text = "上架" if new_status == "PUBLISHED" else "下架"
    return success_response({"id": f.id, "status": new_status}, message=f"民俗节日已成功{action_text}")

@router.delete("/admin/festivals/{festival_id}")
def delete_festival(
    festival_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """运营管理后台：删除民俗节日"""
    f = db.query(FolkFestival).filter(FolkFestival.id == festival_id).first()
    if not f:
        return error_response(code=4040, message="民俗节日不存在")

    db.delete(f)
    db.commit()
    return success_response(message="民俗节日已删除")
