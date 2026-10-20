"""Resolve owned generated task images for the existing collection store."""
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.file_urls import split_signature
from app.models.entities import AiTask, Asset
from app.models.mobile import UserCollection

RESULT_URL_FIELDS = ("colored_image_url", "rendered_image_url", "image_url", "mesh_3d_url", "vector_svg_url")
COLLECTABLE_TOOLS = {"SHADOW_PUPPET", "BRONZE", "EMBROIDERY", "LACQUER", "MESH_3D", "SILHOUETTE"}
IMAGE_SUFFIXES = (".svg", ".png", ".jpg", ".jpeg", ".webp")


def task_result_url(task: AiTask) -> str | None:
    """Best single preview URL for a task, in display priority order."""
    result = task.result_summary_json
    if not isinstance(result, dict):
        return None
    for field in RESULT_URL_FIELDS:
        if isinstance(result.get(field), str):
            return result[field]
    model = result.get("model")
    if isinstance(model, dict) and isinstance(model.get("url"), str):
        return model["url"]
    return None


def task_cover_url(task: AiTask) -> str | None:
    """A URL an <img> can actually render. 3D works only hold a GLB, so they get no cover."""
    url = task_result_url(task)
    if url and split_signature(url)[0].lower().endswith(IMAGE_SUFFIXES):
        return url
    return None


def _generated_urls(node, prefix: str) -> set[str]:
    """Every file this task wrote, wherever it sits in the result payload.

    A fixed field list used to miss the line-art and paper-template SVGs, so deleting a
    work left those files and their asset rows behind.  The prefix is the task's own
    ``generated/<task_id>_`` so a reference to another work's file (a chained sketch)
    is never swept up with it.
    """
    if isinstance(node, str):
        return {node} if node.startswith(prefix) else set()
    if isinstance(node, dict):
        return set().union(*(_generated_urls(value, prefix) for value in node.values())) if node else set()
    if isinstance(node, (list, tuple)):
        return set().union(*(_generated_urls(value, prefix) for value in node)) if node else set()
    return set()


def task_result_urls(task: AiTask) -> set[str]:
    result = task.result_summary_json
    named = ({result[field] for field in RESULT_URL_FIELDS if isinstance(result.get(field), str)}
             if isinstance(result, dict) else set())
    owned = _generated_urls(result, f"/static/generated/{task.task_id}_")
    return {split_signature(url)[0] for url in named | owned}


def task_image_asset(db: Session, task: AiTask):
    if task.status != "SUCCESS":
        return None
    for url in sorted(task_result_urls(task)):
        asset = (db.query(Asset).filter_by(file_url=url, created_by=task.user_id)
                 .order_by(Asset.id).first())
        if asset:
            return asset
    return None


def task_collected(db: Session, task: AiTask) -> bool:
    asset = task_image_asset(db, task)
    return bool(asset and db.get(UserCollection, (task.user_id, "ASSET", asset.id)))


def owned_task_for_asset(db: Session, asset: Asset, user_id: int):
    match = re.fullmatch(r"generated/([0-9a-f]{32})_[a-z_]+\.(?:svg|png|jpg|webp)", asset.object_key or "")
    urls = {split_signature(asset.file_url or "")[0]}
    candidates = (db.query(AiTask).filter(AiTask.user_id == user_id, AiTask.status == "SUCCESS",
                                          AiTask.tool_type.in_(COLLECTABLE_TOOLS)).all() if asset.created_by == user_id else [])
    for task in candidates:
        if match and task.task_id != match.group(1):
            continue
        if urls & task_result_urls(task):
            return task
    raise HTTPException(404, "创作内容不存在")
