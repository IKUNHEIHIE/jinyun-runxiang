"""Resolve owned generated task images for the existing collection store."""
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.entities import AiTask, Asset
from app.models.mobile import UserCollection


def task_image_asset(db: Session, task: AiTask):
    result = task.result_summary_json
    if task.status != "SUCCESS" or not isinstance(result, dict):
        return None
    url = result.get("colored_image_url")
    return db.query(Asset).filter_by(file_url=url, created_by=task.user_id).order_by(Asset.id).first() if url else None


def task_collected(db: Session, task: AiTask) -> bool:
    asset = task_image_asset(db, task)
    return bool(asset and db.get(UserCollection, (task.user_id, "ASSET", asset.id)))


def owned_task_for_asset(db: Session, asset: Asset, user_id: int):
    match = re.fullmatch(r"generated/([0-9a-f]{32})_[a-z_]+\.(?:svg|png|jpg|webp)", asset.object_key or "")
    task = db.get(AiTask, match.group(1)) if match else None
    if (asset.created_by != user_id or not task or task.user_id != user_id or
            task.status != "SUCCESS" or task.tool_type not in {"SHADOW_PUPPET","BRONZE","EMBROIDERY","LACQUER"} or
            not isinstance(task.result_summary_json, dict) or
            task.result_summary_json.get("colored_image_url") != asset.file_url):
        raise HTTPException(404, "创作内容不存在")
    return task
