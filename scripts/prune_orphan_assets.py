"""Report or delete uploaded assets no longer referenced anywhere.

Dry-run by default. Use --delete only after reviewing the JSON report.
Only rows under backend/static/uploads and older than the cutoff are eligible.
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import String, cast

from app.core.database import SessionLocal
from app.models.entities import (
    AiTask, Asset, AssignmentSubmission, BannerConfig, CommunityPost,
    CommunityTopic, Course, CourseChapter, FolkFestival, HeritageLandmark,
    PhilanthropySupply, Product, SysUser, UserProfile,
)
from app.models.mobile import CommunityPostDetail, ExchangeItem, HeritageEntry

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = (ROOT / "backend" / "static" / "uploads").resolve()

URL_REFERENCES = (
    (SysUser, SysUser.avatar_url),
    (Course, Course.cover_url),
    (CourseChapter, CourseChapter.video_url),
    (CommunityTopic, CommunityTopic.cover_url),
    (CommunityPost, CommunityPost.cover_url),
    (CommunityPost, CommunityPost.rural_original_url),
    (HeritageLandmark, HeritageLandmark.cover_url),
    (Product, Product.cover_url),
    (BannerConfig, BannerConfig.image_url),
    (FolkFestival, FolkFestival.cover_url),
    (PhilanthropySupply, PhilanthropySupply.photo_url),
    (HeritageEntry, HeritageEntry.cover_url),
    (HeritageEntry, HeritageEntry.model_url),
    (ExchangeItem, ExchangeItem.cover_url),
)
ASSET_ID_REFERENCES = (
    (Course, Course.cover_asset_id),
    (AssignmentSubmission, AssignmentSubmission.asset_id),
)
JSON_REFERENCES = (
    (AiTask, AiTask.input_json),
    (AiTask, AiTask.result_summary_json),
    (UserProfile, UserProfile.avatar_config_json),
    (CommunityPostDetail, CommunityPostDetail.gallery_json),
)


def is_referenced(db, asset):
    if not asset.file_url:
        return True
    for model, column in URL_REFERENCES:
        if db.query(model.id).filter(column == asset.file_url).first():
            return True
    for model, column in ASSET_ID_REFERENCES:
        if db.query(model.id).filter(column == asset.id).first():
            return True
    for model, column in JSON_REFERENCES:
        if db.query(model).filter(cast(column, String).contains(asset.file_url)).first():
            return True
    return False


def file_path(asset):
    key = asset.object_key or ""
    if not key.startswith("uploads/"):
        return None
    path = (UPLOADS / key[len("uploads/"):]).resolve()
    return path if UPLOADS in path.parents else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="delete eligible rows and files")
    parser.add_argument("--older-than-hours", type=float, default=24)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--id", type=int, action="append", default=[],
                        help="only inspect the given asset id (repeatable)")
    args = parser.parse_args()
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=args.older_than_hours)
    report = {"cutoff": cutoff.isoformat() + "Z", "dry_run": not args.delete,
              "scanned": 0, "referenced": 0, "unsafe": 0, "orphans": [], "deleted": 0, "errors": []}
    with SessionLocal() as db:
        query = db.query(Asset).filter(Asset.object_key.like("uploads/%"),
                                       Asset.created_at <= cutoff).order_by(Asset.id)
        if args.id:
            query = query.filter(Asset.id.in_(args.id))
        if args.limit > 0:
            query = query.limit(args.limit)
        for asset in query.all():
            report["scanned"] += 1
            path = file_path(asset)
            if path is None:
                report["unsafe"] += 1
                report["errors"].append({"id": asset.id, "error": "unsafe object_key", "object_key": asset.object_key})
                continue
            if is_referenced(db, asset):
                report["referenced"] += 1
                continue
            item = {"id": asset.id, "file_url": asset.file_url, "object_key": asset.object_key,
                    "created_by": asset.created_by, "created_at": asset.created_at.isoformat(),
                    "file_exists": path.is_file()}
            report["orphans"].append(item)
            if not args.delete:
                continue
            try:
                db.delete(asset)
                db.commit()
                if path.is_file():
                    path.unlink()
                report["deleted"] += 1
            except OSError as exc:
                db.rollback()
                report["errors"].append({"id": asset.id, "error": str(exc)})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
