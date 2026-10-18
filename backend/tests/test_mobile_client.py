"""Exercise real HTTP/database flows in a fresh, isolated database per test."""
import os
import secrets
from datetime import datetime, timedelta

os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(48))
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.entities import (
    SysUser, UserGrowth, Course, CommunityPost, TeacherClass, Assignment, Asset,
    ClassMember, GrowthEvent, AssignmentSubmission, AssignmentReview, AiTask,
)
from app.models.mobile import HeritageEntry, UserCollection, UserFollow, CourseRating, UserFeedback
from app.models.mobile import ExchangeItem, EnergyExchange, WalkSession


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    def isolated_db():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = isolated_db
    with sessions() as db:
        password = hash_password("test-password-123")
        db.add_all([SysUser(id=i, username=f"user-{i}", nickname=f"name-{i}", password_hash=password,
                            role_code=role, token_version=0) for i, role in
                    [(1, "ADMIN"), (2, "TEACHER"), (3, "STUDENT"), (4, "STUDENT"), (5, "TEACHER")]])
        db.add_all([
            UserGrowth(user_id=3, energy_value=100),
            HeritageEntry(id=1, title="杨柳青年画", category="NEW_YEAR_PAINTING", summary="半印半画", content_json={}),
            HeritageEntry(id=2, title="未发布", category="DRAFT", status="DRAFT", content_json={}),
            HeritageEntry(id=3, title="穆桂英挂帅", category="CLAY_FIGURINE", era="泥人张 · 彩塑", content_json={}),
            Course(id=1, title="非遗课程", category="BRONZE", status="PUBLISHED"),
            Course(id=2, title="未发布课程", category="BRONZE", status="OFFLINE"),
            CommunityPost(id=1, user_id=4, title="公开作品", status="APPROVED"),
            CommunityPost(id=2, user_id=4, title="待审作品", status="PENDING_REVIEW"),
            TeacherClass(id=1, teacher_id=2, name="美育课堂", grade="小学三年级", invite_code="TEST1234"),
            Assignment(id=1, class_id=1, teacher_id=2, title="非遗观察", description="观察和记录纹样",
                       deadline=datetime.utcnow() + timedelta(days=1)),
            Asset(id=1, asset_type="IMAGE", object_key="x", mime_type="image/png", created_by=4),
        ])
        db.commit()
    with TestClient(app) as c:
        c.sessions = sessions
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def auth(uid=3, role="STUDENT"):
    return {"Authorization": "Bearer " + create_access_token(
        {"sub": str(uid), "user_id": uid, "role_code": role, "token_version": 0})}


def test_course_badge_requires_one_whole_published_course_and_awards_once(client):
    from app.models.entities import Badge, CourseChapter, LearningProgress, UserBadge
    with client.sessions() as db:
        db.add_all([
            Badge(id=8, code="BADGE_COURSE_BRONZE", name="青铜识者", description="完成青铜课程", icon_url="/static/design/bronze.png"),
            Course(id=3, title="第二门青铜", category="BRONZE", status="PUBLISHED"),
            Course(id=4, title="空课程", category="BRONZE", status="PUBLISHED"),
            CourseChapter(id=1, course_id=1, seq=1, title="第一章", duration_seconds=60),
            CourseChapter(id=2, course_id=1, seq=2, title="第二章", duration_seconds=60),
            CourseChapter(id=3, course_id=3, seq=1, title="另一门第一章", duration_seconds=60),
            CourseChapter(id=4, course_id=3, seq=2, title="另一门第二章", duration_seconds=60),
            CourseChapter(id=5, course_id=2, title="下架课程", duration_seconds=60),
            LearningProgress(user_id=3, course_id=3, chapter_id=3, completed=True),
            LearningProgress(user_id=3, course_id=2, chapter_id=5, completed=True),
            LearningProgress(user_id=4, course_id=1, chapter_id=1, completed=True),
            LearningProgress(user_id=4, course_id=1, chapter_id=2, completed=True),
        ])
        db.commit()
    payload = {"course_id":1, "chapter_id":1, "position_seconds":60, "duration_seconds":60, "completed":True}
    first = client.post("/api/courses/progress", headers=auth(), json=payload).json()["data"]
    assert first["badges_unlocked"] == []
    partial = payload | {"chapter_id":2, "position_seconds":30, "completed":False}
    assert client.post("/api/courses/progress", headers=auth(), json=partial).json()["data"]["badges_unlocked"] == []
    catalog = client.get("/api/mobile/badges", headers=auth()).json()["data"][0]
    assert not catalog["unlocked"] and catalog["course_progress"]["completed_courses"] == 0
    assert catalog["course_progress"]["available_courses"] == 2
    finished = client.post("/api/courses/progress", headers=auth(), json=payload | {"chapter_id":2}).json()["data"]
    assert finished["badges_unlocked"] == ["BADGE_COURSE_BRONZE"]
    assert client.post("/api/courses/progress", headers=auth(), json=payload | {"chapter_id":2}).json()["data"]["badges_unlocked"] == []
    with client.sessions() as db:
        assert db.query(UserBadge).filter_by(user_id=3, badge_id=8).count() == 1
        assert db.query(UserBadge).filter_by(user_id=4).count() == 0
        assert db.get(UserGrowth, 3).energy_value == 120  # Existing chapter rewards only.
    owned = client.get("/api/mobile/badges", headers=auth()).json()["data"][0]
    assert owned["unlocked"] and owned["course_progress"]["completed_courses"] == 1
    # Historical awards survive teacher changes; progress reflects current chapters.
    with client.sessions() as db:
        db.add(CourseChapter(course_id=1, seq=3, title="新增章", duration_seconds=60))
        db.commit()
    changed = client.get("/api/mobile/badges", headers=auth()).json()["data"][0]
    assert changed["unlocked"] and changed["course_progress"]["completed_courses"] == 0


@pytest.mark.parametrize("category,code", [
    ("SHADOW_PUPPET","BADGE_COURSE_SHADOW_PUPPET"), ("BRONZE","BADGE_COURSE_BRONZE"),
    ("PAPER_CUTTING","BADGE_COURSE_PAPER_CUTTING"), ("EMBROIDERY","BADGE_COURSE_EMBROIDERY"),
    ("CERAMICS","BADGE_COURSE_CERAMICS"),
])
def test_all_design_course_badges_unlock_from_offline_sync_without_identity_leaks(client, category, code):
    from app.models.entities import Badge, CourseChapter, UserBadge
    with client.sessions() as db:
        db.get(Course, 1).category = category
        db.add_all([Badge(id=8, code=code, name="专题徽章", description="全部章节", icon_url="/static/design/original.png"),
                    CourseChapter(id=1, course_id=1, seq=1, title="第一章", duration_seconds=60),
                    CourseChapter(id=2, course_id=1, seq=2, title="第二章", duration_seconds=60)])
        db.commit()
    event_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    def event(chapter):
        return {"event_id":f"badge-offline-{chapter}", "event_type":"PROGRESS_UPDATE", "event_time":event_time,
                "payload":{"course_id":1,"chapter_id":chapter,"position_seconds":60,"duration_seconds":60,"completed":True}}
    request = {"events":[event(2), event(1)]}
    for _ in range(2):
        result = client.post("/api/courses/sync-offline", headers=auth(), json=request).json()["data"]
        assert result["synced_count"] == 2 and not result["conflict_event_ids"]
    with client.sessions() as db:
        assert db.query(UserBadge).filter_by(user_id=3, badge_id=8).count() == 1
        assert db.get(UserGrowth, 3).energy_value == 120
    owner = client.get("/api/mobile/badges", headers=auth()).json()["data"][0]
    other = client.get("/api/mobile/badges", headers=auth(4)).json()["data"][0]
    guest = client.get("/api/mobile/badges").json()["data"][0]
    assert owner["unlocked"] and owner["course_progress"]["completed_courses"] == 1
    assert not other["unlocked"] and other["course_progress"]["completed_courses"] == 0
    assert not guest["unlocked"] and guest["course_progress"]["completed_courses"] is None


def test_map_milestones_distinguish_visits_payment_and_user(client):
    from app.models.entities import HeritageLandmark, ActivityCheckin, Product, OrderMain, OrderItem
    with client.sessions() as db:
        db.add_all([
            HeritageLandmark(id=1, name="基地一", category="皮影", address="开发地址一", district="蓟州区", latitude=40, longitude=117, geofence_radius_meters=100),
            HeritageLandmark(id=2, name="基地二", category="青铜", address="开发地址二", district="武清区", latitude=39, longitude=117, geofence_radius_meters=100),
            ActivityCheckin(user_id=3, landmark_id=1, latitude=40, longitude=117, distance_meters=0),
            ActivityCheckin(user_id=3, landmark_id=1, latitude=40, longitude=117, distance_meters=0),
            ActivityCheckin(user_id=3, landmark_id=2, latitude=40, longitude=117, distance_meters=2000),
            ActivityCheckin(user_id=4, landmark_id=2, latitude=39, longitude=117, distance_meters=0),
            Product(id=1, name="开发农产", category="AGRI_PRODUCT", cover_url="/static/images/test.png"),
            OrderMain(id=1, order_no="MAP-PENDING", user_id=3, status="CREATED"),
            OrderMain(id=2, order_no="MAP-CANCELLED", user_id=3, status="CANCELLED"),
            OrderMain(id=3, order_no="MAP-OTHER-PAID", user_id=4, status="PAID"),
        ])
        for order_id in [1, 2, 3]:
            db.add(OrderItem(order_id=order_id, product_id=1, sku_id=1, product_name="开发农产", sku_name="开发", price_cents=100, quantity=1))
        db.commit()
    first = client.get("/api/mobile/me/footprints", headers=auth()).json()["data"]
    assert first["landmark_count"] == 2 and first["agri_order_count"] == 2
    assert first["paid_agri_order_count"] == 0
    states = {m["code"]: m for m in first["milestones"]}
    assert states["FIRST_VISIT"]["completed"] and states["FIRST_ONSITE"]["completed"]
    assert states["FIRST_ONSITE"]["current"] == 1
    assert not states["FIRST_AGRI_PURCHASE"]["completed"] and not states["ALL_ACTIVE_ONSITE"]["completed"]
    with client.sessions() as db:
        db.get(OrderMain, 1).status = "SHIPPED"
        db.add(ActivityCheckin(user_id=3, landmark_id=2, latitude=39, longitude=117, distance_meters=0))
        db.commit()
    result = client.get("/api/mobile/me/footprints", headers=auth()).json()["data"]
    assert result["paid_agri_order_count"] == 1
    assert all(m["completed"] for m in result["milestones"])
    with client.sessions() as db:
        for landmark in db.query(HeritageLandmark):
            landmark.status = "INACTIVE"
        db.commit()
    empty_catalog = client.get("/api/mobile/me/footprints", headers=auth()).json()["data"]
    all_sites = next(m for m in empty_catalog["milestones"] if m["code"] == "ALL_ACTIVE_ONSITE")
    assert all_sites["target"] == 0 and not all_sites["completed"]


def test_my_reviews_only_returns_own_persisted_ratings(client):
    with client.sessions() as db:
        db.add_all([CourseRating(user_id=3, course_id=1, score=4, comment="观察纹样很有收获"),
                    CourseRating(user_id=4, course_id=1, score=2, comment="另一用户的评价")])
        db.commit()
    assert client.get("/api/mobile/me/reviews").status_code == 401
    result = client.get("/api/mobile/me/reviews", headers=auth()).json()["data"]
    assert len(result) == 1 and result[0]["course_id"] == 1
    assert result[0]["rating"] == 4 and result[0]["comment"] == "观察纹样很有收获"


def test_learning_days_survive_repeated_chapter_updates_and_midnight(client, monkeypatch):
    from app.api import course as course_api
    from app.models.entities import CourseChapter, LearningProgress
    from app.models.mobile import LearningDay

    class Clock(datetime):
        moment = datetime(2026, 10, 14, 15, 59)

        @classmethod
        def utcnow(cls):
            return cls.moment

    monkeypatch.setattr(course_api, "datetime", Clock)
    with client.sessions() as db:
        db.add(CourseChapter(id=1, course_id=1, title="第一章", duration_seconds=60))
        db.commit()
    payload = {"course_id": 1, "chapter_id": 1, "position_seconds": 0, "duration_seconds": 60}
    assert client.post("/api/courses/progress", headers=auth(), json=payload).status_code == 200
    assert client.get("/api/mobile/me/summary", headers=auth()).json()["data"]["learning_days"] == 0
    for _ in range(2):
        assert client.post("/api/courses/progress", headers=auth(), json=payload | {"position_seconds": 2}).status_code == 200
    assert client.get("/api/mobile/me/summary", headers=auth()).json()["data"]["learning_days"] == 1
    Clock.moment = datetime(2026, 10, 14, 16, 1)
    assert client.post("/api/courses/progress", headers=auth(), json=payload | {"position_seconds": 4}).status_code == 200
    assert client.get("/api/mobile/me/summary", headers=auth()).json()["data"]["learning_days"] == 2
    assert client.get("/api/mobile/me/summary", headers=auth(4)).json()["data"]["learning_days"] == 0
    with client.sessions() as db:
        assert db.query(LearningProgress).count() == 1
        assert {str(row.day) for row in db.query(LearningDay).all()} == {"2026-10-14", "2026-10-15"}


def test_offline_learning_days_use_event_timezone_and_ignore_retries(client):
    from app.models.entities import CourseChapter, LearningProgress, OfflineSyncEvent
    from app.models.mobile import LearningDay
    with client.sessions() as db:
        db.add(CourseChapter(id=1, course_id=1, title="第一章", duration_seconds=60))
        db.commit()
    payload = {"course_id": 1, "chapter_id": 1, "position_seconds": 60, "duration_seconds": 60, "completed": True}
    newer = {"event_id": "day-newer", "event_type": "PROGRESS_UPDATE", "event_time": "2026-10-12T16:30:00Z", "payload": payload}
    older = newer | {"event_id": "day-older", "event_time": "2026-10-12T23:30:00+08:00", "payload": payload | {"position_seconds": 2, "completed": False}}
    zero = older | {"event_id": "day-zero", "event_time": "2026-10-11T00:00:00Z", "payload": payload | {"position_seconds": 0, "completed": False}}
    invalid = older | {"event_id": "day-invalid", "event_time": "bad-date"}
    future = older | {"event_id": "day-future", "event_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"}
    for _ in range(2):
        result = client.post("/api/courses/sync-offline", headers=auth(), json={"events": [newer, older, zero, invalid, future]})
        assert result.status_code == 200
        data = result.json()["data"]
        assert data["success_event_ids"] == ["day-newer", "day-older", "day-zero"]
        assert data["conflict_event_ids"] == ["day-invalid", "day-future"]
    assert client.get("/api/mobile/me/summary", headers=auth()).json()["data"]["learning_days"] == 2
    assert client.get("/api/mobile/me/summary", headers=auth(4)).json()["data"]["learning_days"] == 0
    with client.sessions() as db:
        assert {str(row.day) for row in db.query(LearningDay).all()} == {"2026-10-12", "2026-10-13"}
        progress = db.query(LearningProgress).one()
        assert progress.position_seconds == 60 and progress.completed
        assert progress.last_learned_at == datetime(2026, 10, 12, 16, 30)
        assert db.get(OfflineSyncEvent, "day-older").event_time == datetime(2026, 10, 12, 15, 30)
        assert db.query(OfflineSyncEvent).count() == 3
        assert db.get(UserGrowth, 3).energy_value == 110


def test_teacher_assignment_input_bounds(client):
    payload = {"class_id": 1, "title": "观察记录", "description": "记录纹样寓意"}
    for patch in [{"deadline_days": -1}, {"deadline_days": 366}, {"title": ""}, {"type": "UNKNOWN"}, {"tool_type": "UNKNOWN"}]:
        assert client.post("/api/teacher/assignments", headers=auth(2, "TEACHER"), json=payload | patch).status_code == 422
    assert client.post("/api/teacher/assignments", headers=auth(), json=payload).status_code == 403


def test_artwork_gallery_metadata_ownership_and_review_evidence(client):
    from app.models.mobile import CommunityPostDetail
    from app.models.entities import ContentReview
    payload = {"title":"青花习作","content":"记录青花的线条与色彩","category":"CERAMICS",
               "cover_url":"https://example.com/cover.png", "gallery":["https://example.com/detail.png"],
               "specifications":[{"label":"尺寸规格","value":"高38cm"}],
               "appreciation":[{"title":"线条","body":"观察纹样的疏密关系"}]}
    result = client.post("/api/community/posts", headers=auth(), json=payload)
    assert result.status_code == 200 and result.json()["data"]["status"] == "APPROVED"
    post_id = result.json()["data"]["id"]
    detail = client.get(f"/api/community/posts/{post_id}").json()["data"]
    assert detail["gallery"] == [payload["cover_url"], *payload["gallery"]]
    assert detail["specifications"] == payload["specifications"] and detail["appreciation"] == payload["appreciation"]
    with client.sessions() as db:
        assert db.get(CommunityPostDetail, post_id).gallery_json == detail["gallery"]
        audit = db.query(ContentReview).filter_by(target_id=post_id).one().ai_analysis_json
        assert audit["image_review_status"] == "NOT_CONFIGURED" and "image_nsfw_prob" not in audit
        db.add(Asset(id=2, asset_type="IMAGE", object_key="other", file_url="/static/uploads/other.png", mime_type="image/png", created_by=4)); db.commit()
    assert client.post("/api/community/posts", headers=auth(), json=payload | {"cover_url":"/static/uploads/other.png"}).status_code == 404
    assert client.post("/api/community/posts", headers=auth(), json=payload | {"cover_url":"javascript:alert(1)"}).status_code == 422
    assert client.post("/api/community/posts", headers=auth(), json=payload | {"source_task_id":"foreign-task"}).status_code == 404


def test_comment_paging_reply_scope_and_likes(client):
    from app.models.entities import CommunityComment
    with client.sessions() as db:
        db.add_all([CommunityComment(id=i, post_id=1, user_id=4, content=f"留言{i}") for i in range(1,24)])
        db.add(CommunityComment(id=99, post_id=2, user_id=4, content="私有留言")); db.commit()
    page1 = client.get("/api/community/posts/1/comments?pageSize=20").json()["data"]
    page2 = client.get("/api/community/posts/1/comments?pageSize=20&page=2").json()["data"]
    assert page1["total"] == 23 and len(page1["list"]) == 20 and len(page2["list"]) == 3
    assert not {c["id"] for c in page1["list"]} & {c["id"] for c in page2["list"]}
    invalid = client.post("/api/community/posts/1/comments", headers=auth(), json={"content":"回复","reply_to_id":99})
    assert invalid.status_code == 422
    reply = client.post("/api/community/posts/1/comments", headers=auth(), json={"content":"谢谢分享","reply_to_id":1})
    assert reply.status_code == 200
    latest = client.get("/api/community/posts/1/comments", headers=auth()).json()["data"]["list"][0]
    assert latest["reply_to"] == {"id":1,"nickname":"name-4","content":"留言1"}
    assert client.post("/api/community/comments/1/like").status_code == 401
    assert client.post("/api/community/comments/1/like", headers=auth()).json()["data"] == {"is_liked":True,"like_count":1}
    liked = client.get("/api/community/posts/1/comments?page=2", headers=auth()).json()["data"]["list"]
    assert next(c for c in liked if c["id"] == 1)["is_liked"] is True
    assert client.post("/api/community/comments/1/like", headers=auth()).json()["data"] == {"is_liked":False,"like_count":0}


def test_pending_post_interactions_and_comment_bounds(client):
    from app.models.entities import CommunityComment
    with client.sessions() as db:
        db.add(CommunityComment(id=99, post_id=2, user_id=4, content="未发布留言")); db.commit()
    assert client.get("/api/community/posts/2/comments").status_code == 404
    assert client.get("/api/community/posts/2/related").status_code == 404
    assert client.post("/api/community/posts/2/like", headers=auth()).status_code == 404
    assert client.post("/api/community/comments/99/like", headers=auth()).status_code == 404
    assert client.post("/api/community/posts/2/comments", headers=auth(), json={"content":"回复"}).status_code == 404
    for content in ["   ", "x"*1001]:
        assert client.post("/api/community/posts/1/comments", headers=auth(), json={"content":content}).status_code == 422
    assert client.get("/api/community/posts/1/comments?pageSize=1000").status_code == 422
    assert client.post("/api/community/reports", headers=auth(), json={"post_id":999,"reason":"不存在"}).status_code == 404


def test_related_artworks_exclude_private_and_current(client):
    with client.sessions() as db:
        db.get(CommunityPost, 1).category = "CERAMICS"
        db.add_all([CommunityPost(id=5, user_id=4, title="同类作品", category="CERAMICS", status="APPROVED"),
                    CommunityPost(id=6, user_id=4, title="待审核作品", category="CERAMICS", status="PENDING_REVIEW"),
                    CommunityPost(id=7, user_id=4, title="其他分类", category="BRONZE", status="APPROVED")]); db.commit()
    related = client.get("/api/community/posts/1/related").json()["data"]
    assert [p["id"] for p in related] == [5]


def test_geographic_checkin_bounds_rewards_and_honest_badge(client):
    from app.models.entities import HeritageLandmark, Badge, UserBadge
    with client.sessions() as db:
        db.add(HeritageLandmark(id=1, name="联调地标", category="年画", address="开发测试", district="西青区", latitude=39.14, longitude=117.00, geofence_radius_meters=500))
        db.add(Badge(id=8, code="BADGE_HERITAGE_PIONEER", name="乡村美育使者", description="现场签到", icon_url="/static/test.svg"))
        db.commit()
    bad = client.post("/api/activities/checkin", headers=auth(), json={"landmark_id":1,"latitude":91,"longitude":117})
    assert bad.status_code == 422
    wrong = client.post("/api/activities/checkin", headers=auth(), json={"landmark_id":1,"activity_id":999,"latitude":39.14,"longitude":117})
    assert wrong.status_code == 422
    cloud = client.post("/api/activities/checkin", headers=auth(), json={"landmark_id":1,"latitude":0,"longitude":0}).json()["data"]
    assert cloud["energy_added"] == 30 and cloud["badge_unlocked"] is None and not cloud["in_geofence"]
    onsite = client.post("/api/activities/checkin", headers=auth(), json={"landmark_id":1,"latitude":39.14,"longitude":117,"accuracy":5}).json()["data"]
    assert onsite["energy_added"] == 0 and onsite["badge_unlocked"] == "乡村美育使者" and onsite["in_geofence"]
    again = client.post("/api/activities/checkin", headers=auth(), json={"landmark_id":1,"latitude":39.14,"longitude":117,"accuracy":5}).json()["data"]
    assert again["badge_unlocked"] is None
    with client.sessions() as db:
        assert db.get(UserGrowth,3).energy_value == 130
        assert db.query(UserBadge).filter_by(user_id=3).one().badge_id == 8


def test_checkin_accuracy_persists_and_only_confirmed_onsite_unlocks(client):
    from app.models.entities import HeritageLandmark, Badge, UserBadge, ActivityCheckin
    with client.sessions() as db:
        db.add(HeritageLandmark(id=1, name="精度测试基地", category="年画", address="测试地址", district="西青区", latitude=39.14, longitude=117, geofence_radius_meters=50))
        db.add(Badge(id=8, code="BADGE_HERITAGE_PIONEER", name="现场使者", description="现场打卡", icon_url="/static/test.svg"))
        db.commit()
    payload = {"landmark_id": 1, "latitude": 39.14, "longitude": 117}
    for accuracy in [-1, 100001]:
        assert client.post("/api/activities/checkin", headers=auth(), json={**payload, "accuracy": accuracy}).status_code == 422
    for accuracy in [None, 1000]:
        body = payload if accuracy is None else {**payload, "accuracy": accuracy}
        result = client.post("/api/activities/checkin", headers=auth(), json=body).json()["data"]
        assert result["geofence_status"] == "UNCERTAIN" and not result["in_geofence"] and result["badge_unlocked"] is None
    uncertain = client.get("/api/mobile/me/footprints", headers=auth()).json()["data"]
    assert all(r["geofence_status"] == "UNCERTAIN" and not r["in_geofence"] for r in uncertain["list"])
    assert not next(m for m in uncertain["milestones"] if m["code"] == "FIRST_ONSITE")["completed"]
    overlap = client.post("/api/activities/checkin", headers=auth(), json={**payload, "latitude":39.1406, "accuracy":100}).json()["data"]
    assert overlap["distance_meters"] > 50 and overlap["geofence_status"] == "UNCERTAIN"
    cloud = client.post("/api/activities/checkin", headers=auth(), json={**payload, "latitude":39.1406, "accuracy":5}).json()["data"]
    assert cloud["geofence_status"] == "CLOUD" and not cloud["in_geofence"]
    confirmed = client.post("/api/activities/checkin", headers=auth(), json={**payload, "accuracy":5}).json()["data"]
    assert confirmed["geofence_status"] == "ONSITE" and confirmed["in_geofence"] and confirmed["badge_unlocked"] == "现场使者"
    assert confirmed["energy_added"] == 0
    with client.sessions() as db:
        assert db.get(UserGrowth, 3).energy_value == 130
        assert db.query(UserBadge).filter_by(user_id=3).count() == 1
        assert db.query(ActivityCheckin).filter_by(user_id=3, geofence_status="UNCERTAIN").count() == 3
        db.get(HeritageLandmark, 1).geofence_radius_meters = 0
        db.commit()
    records = client.get("/api/mobile/me/footprints", headers=auth()).json()["data"]
    assert records["list"][0]["geofence_status"] == "ONSITE" and records["list"][0]["accuracy_meters"] == 5
    assert next(m for m in records["milestones"] if m["code"] == "FIRST_ONSITE")["completed"]


def test_walking_previous_day_closes_before_starting_today(client):
    first = client.post("/api/mobile/walks", headers=auth()).json()["data"]
    with client.sessions() as db:
        record = db.get(WalkSession, first["id"])
        record.started_at = datetime.utcnow() - timedelta(days=2)
        record.active_seconds = 120
        db.commit()
    current = client.post("/api/mobile/walks", headers=auth()).json()["data"]
    assert current["id"] != first["id"] and current["active_seconds"] == 0
    history = client.get("/api/mobile/walks", headers=auth()).json()["data"]
    assert history["today_seconds"] == 0 and history["total_seconds"] == 120
    assert next(r for r in history["list"] if r["id"] == first["id"])["status"] == "COMPLETED"


def test_walking_totals_cover_history_and_old_day_reports_are_capped(client, monkeypatch):
    from app.api import mobile_walking as walking_api
    from datetime import timezone
    class Clock(datetime):
        moment = datetime(2026, 10, 16, 16, 5)
        @classmethod
        def utcnow(cls): return cls.moment
        @classmethod
        def now(cls, tz=None):
            instant = cls.moment.replace(tzinfo=timezone.utc)
            return instant.astimezone(tz) if tz else cls.moment
    monkeypatch.setattr(walking_api, "datetime", Clock)
    with client.sessions() as db:
        db.add_all([WalkSession(user_id=3, active_seconds=10, distance_meters=5, status="COMPLETED", started_at=Clock.moment-timedelta(minutes=1)) for _ in range(120)])
        record = WalkSession(user_id=3, started_at=datetime(2026, 10, 16, 15, 59), active_seconds=0)
        db.add(record); db.flush(); previous_id = record.id
        db.commit()
    history = client.get("/api/mobile/walks", headers=auth()).json()["data"]
    assert len(history["list"]) == 121 and history["today_seconds"] == 1200
    assert history["total_seconds"] == 1200 and history["total_distance_meters"] == 600
    capped = client.put(f"/api/mobile/walks/{previous_id}", headers=auth(), json={"active_seconds":600,"completed":True}).json()["data"]
    assert capped["active_seconds"] == 60 and capped["status"] == "COMPLETED"
    assert client.get("/api/mobile/walks", headers=auth()).json()["data"]["today_seconds"] == 1200


def test_pathfinder_badge_uses_only_one_shanghai_days_total_and_unlocks_once(client, monkeypatch):
    from app.api import mobile_walking as walking_api
    from app.models.entities import Badge, UserBadge
    from datetime import timezone
    class Clock(datetime):
        moment = datetime(2026, 10, 17, 4)
        @classmethod
        def utcnow(cls): return cls.moment
        @classmethod
        def now(cls, tz=None):
            instant = cls.moment.replace(tzinfo=timezone.utc)
            return instant.astimezone(tz) if tz else cls.moment
    monkeypatch.setattr(walking_api, "datetime", Clock)
    with client.sessions() as db:
        db.add(Badge(id=9, code="BADGE_WALK_PATHFINDER", name="探路者", description="每日60分钟", icon_url="/static/test.svg"))
        db.add_all([WalkSession(id=18, user_id=3, active_seconds=1800, status="COMPLETED", started_at=Clock.moment-timedelta(hours=2)),
                    WalkSession(id=20, user_id=3, active_seconds=0, started_at=Clock.moment-timedelta(hours=1)),
                    WalkSession(id=19, user_id=4, active_seconds=3600, status="COMPLETED", started_at=Clock.moment-timedelta(days=1)),
                    WalkSession(id=21, user_id=4, active_seconds=0, started_at=Clock.moment-timedelta(minutes=1))])
        db.commit()
    for _ in range(2):
        assert client.put("/api/mobile/walks/20", headers=auth(), json={"active_seconds":1800}).status_code == 200
    assert client.put("/api/mobile/walks/21", headers=auth(4), json={"active_seconds":10}).status_code == 200
    with client.sessions() as db:
        assert db.query(UserBadge).filter_by(user_id=3, badge_id=9).count() == 1
        assert db.query(UserBadge).filter_by(user_id=4, badge_id=9).count() == 0


def test_heritage_public_search_and_hidden_detail(client):
    stats = client.get("/api/mobile/heritage").json()["data"]["stats"]
    assert stats == {"heritage_projects": 2, "teaching_resources": 1}
    result = client.get("/api/mobile/heritage", params={"keyword": "年画"}).json()["data"]
    assert result["total"] == 1 and result["list"][0]["title"] == "杨柳青年画"
    result = client.get("/api/mobile/heritage", params={"keyword": "泥人张"}).json()["data"]
    assert result["total"] == 1 and result["list"][0]["title"] == "穆桂英挂帅"
    result = client.get("/api/mobile/heritage", params={"keyword": "风筝"}).json()["data"]
    assert result["total"] == 0
    assert client.get("/api/mobile/heritage/2").status_code == 404
    assert client.get("/api/mobile/heritage/999").status_code == 404
    assert client.get("/api/mobile/heritage", params={"page": 0}).status_code == 422


def test_heritage_write_requires_admin_and_persists(client):
    payload = {"title": "泥人张", "category": "CLAY", "content": {"sections": [{"title": "工艺"}]}}
    assert client.post("/api/mobile/heritage", headers=auth(), json=payload).status_code == 403
    result = client.post("/api/mobile/heritage", headers=auth(1, "ADMIN"), json=payload).json()["data"]
    assert client.get(f'/api/mobile/heritage/{result["id"]}').json()["data"]["content"] == payload["content"]


def test_daily_signin_idempotent_and_auth_required(client):
    assert client.post("/api/mobile/me/checkin").status_code == 401
    first = client.post("/api/mobile/me/checkin", headers=auth()).json()["data"]
    second = client.post("/api/mobile/me/checkin", headers=auth()).json()["data"]
    assert first["energy_added"] == 10 and second["energy_added"] == 0
    assert second["energy_value"] == 110 and second["already_checked_in"]
    with client.sessions() as db:
        assert db.query(GrowthEvent).count() == 1


def test_update_profile_cannot_elevate_role(client):
    payload = {"nickname": "小小学徒", "bio": "传承非遗", "role_code": "ADMIN"}
    assert client.put("/api/mobile/me/profile", headers=auth(), json=payload).status_code == 200
    profile = client.get("/api/auth/me", headers=auth()).json()["data"]
    assert profile["nickname"] == "小小学徒" and profile["role_code"] == "STUDENT"


def test_badge_catalog_uses_current_user_unlocks(client):
    from app.models.entities import Badge, UserBadge
    with client.sessions() as db:
        db.add_all([Badge(id=i, code=f"BADGE-{i}", name=f"徽章-{i}", description="完成实际研习解锁",
                          icon_url="/static/badge.svg") for i in [1, 2]])
        db.add_all([UserBadge(user_id=3, badge_id=1), UserBadge(user_id=4, badge_id=2)])
        db.commit()
    guest = client.get("/api/mobile/badges").json()["data"]
    assert len(guest) == 2 and not any(b["unlocked"] for b in guest)
    student = client.get("/api/mobile/badges", headers=auth()).json()["data"]
    assert student[0]["unlocked"] and student[0]["unlocked_at"]
    assert not student[1]["unlocked"] and student[1]["unlocked_at"] is None
    other = client.get("/api/mobile/badges", headers=auth(4)).json()["data"]
    assert not other[0]["unlocked"] and other[1]["unlocked"]


@pytest.mark.parametrize("kind,target", [("COURSE", 1), ("POST", 1), ("HERITAGE", 1)])
def test_collection_toggle_persists_without_duplicates(client, kind, target):
    path = f"/api/mobile/collections/{kind}/{target}"
    assert client.post(path, headers=auth()).json()["data"]["collected"]
    assert len(client.get("/api/mobile/me/collections", headers=auth()).json()["data"]) == 1
    assert not client.post(path, headers=auth()).json()["data"]["collected"]
    with client.sessions() as db:
        assert db.query(UserCollection).count() == 0
        if kind == "POST":
            assert db.get(CommunityPost, 1).favorite_count == 0


def test_heritage_detail_reports_current_user_collection(client):
    assert client.get("/api/mobile/heritage/1").json()["data"]["collected"] is False
    assert client.post("/api/mobile/collections/HERITAGE/1", headers=auth()).json()["data"]["collected"] is True
    assert client.get("/api/mobile/heritage/1", headers=auth()).json()["data"]["collected"] is True
    assert client.get("/api/mobile/heritage/1", headers=auth(4)).json()["data"]["collected"] is False
    assert client.post("/api/mobile/collections/HERITAGE/1", headers=auth()).json()["data"]["collected"] is False
    assert client.get("/api/mobile/heritage/1", headers=auth()).json()["data"]["collected"] is False


def test_collections_do_not_expose_unpublished_content(client):
    for kind in ["COURSE", "POST", "HERITAGE"]:
        assert client.post(f"/api/mobile/collections/{kind}/2", headers=auth()).status_code == 404


def test_follow_and_unfollow_users(client):
    assert client.post("/api/mobile/users/3/follow", headers=auth()).status_code == 422
    assert client.post("/api/mobile/users/999/follow", headers=auth()).status_code == 404
    assert client.post("/api/mobile/users/4/follow", headers=auth()).json()["data"]["following"]
    assert client.get("/api/mobile/me/follows", headers=auth()).json()["data"][0]["id"] == 4
    assert client.get("/api/mobile/me/summary", headers=auth()).json()["data"]["following_count"] == 1
    assert not client.post("/api/mobile/users/4/follow", headers=auth()).json()["data"]["following"]


def test_rating_validation_and_update_instead_of_duplicate(client):
    assert client.put("/api/mobile/courses/1/rating", headers=auth(), json={"score": 6}).status_code == 422
    for score in [4, 5]:
        assert client.put("/api/mobile/courses/1/rating", headers=auth(), json={"score": score}).status_code == 200
    with client.sessions() as db:
        assert db.query(CourseRating).count() == 1
        assert db.get(CourseRating, (3, 1)).score == 5


def test_feedback_is_stored(client):
    assert client.post("/api/mobile/feedback", headers=auth(), json={"content": "希望增加非遗课程"}).status_code == 200
    with client.sessions() as db:
        assert db.query(UserFeedback).one().user_id == 3


def test_feedback_handling_visible_only_to_owner_and_terminal_reply_is_immutable(client):
    first = client.post('/api/mobile/feedback', headers=auth(), json={
        'content':'  课程图集显示问题，请协助查看  ', 'contact':'test contact'}).json()['data']['id']
    client.post('/api/mobile/feedback', headers=auth(4), json={'content':'另一位同学的反馈'})
    admin = auth(1, 'ADMIN')
    page = client.get('/api/mobile/admin/feedback?page_size=1', headers=admin).json()['data']
    assert page['total'] == 2 and len(page['items']) == 1 and page['items'][0]['id'] != first
    endpoint = f'/api/mobile/admin/feedback/{first}'
    processing = client.put(endpoint, headers=admin, json={'status':'PROCESSING'}).json()['data']
    assert processing['handled_by'] == 1 and processing['handled_at'] and not processing['reply_text']
    assert client.put(endpoint, headers=admin, json={'status':'PROCESSING'}).json()['data'] == processing
    own = client.get('/api/mobile/me/feedback', headers=auth()).json()['data']
    assert len(own) == 1 and own[0]['status'] == 'PROCESSING'
    assert own[0]['content'] == '课程图集显示问题，请协助查看'
    assert 'contact' not in own[0] and 'handled_by' not in own[0] and 'user_id' not in own[0]
    reply = '已排查。\n请刷新课程页面；<b>文字按原文显示</b>。'
    resolved = client.put(endpoint, headers=admin, json={'status':'RESOLVED', 'reply_text':reply}).json()['data']
    assert resolved['reply_text'] == reply and resolved['status'] == 'RESOLVED'
    assert client.put(endpoint, headers=admin, json={'status':'RESOLVED', 'reply_text':reply}).json()['data'] == resolved
    assert client.put(endpoint, headers=admin, json={'status':'RESOLVED', 'reply_text':'覆盖旧回复'}).status_code == 409
    assert client.put(endpoint, headers=admin, json={'status':'PROCESSING'}).status_code == 409
    assert client.get('/api/mobile/me/feedback', headers=auth()).json()['data'][0]['reply_text'] == reply
    other = client.get('/api/mobile/me/feedback', headers=auth(4)).json()['data']
    assert len(other) == 1 and other[0]['id'] != first and not other[0]['reply_text']
    filtered = client.get('/api/mobile/admin/feedback?status=RESOLVED', headers=admin).json()['data']
    assert filtered['total'] == 1 and filtered['items'][0]['id'] == first
    with client.sessions() as db:
        record = db.get(UserFeedback, first)
        assert record.reply_text == reply and record.handled_by == 1


def test_feedback_admin_roles_validation_and_missing_records(client):
    record = client.post('/api/mobile/feedback', headers=auth(), json={'content':'课程使用体验建议'}).json()['data']['id']
    endpoint = f'/api/mobile/admin/feedback/{record}'
    assert client.get('/api/mobile/me/feedback').status_code == 401
    for headers in [auth(), auth(2, 'TEACHER')]:
        assert client.get('/api/mobile/admin/feedback', headers=headers).status_code == 403
        assert client.put(endpoint, headers=headers, json={'status':'RESOLVED','reply_text':'已回复'}).status_code == 403
    admin = auth(1, 'ADMIN')
    for body in [{'status':'RESOLVED'}, {'status':'RESOLVED','reply_text':'   '},
                 {'status':'PROCESSING','reply_text':'不能提前发布'}, {'status':'PENDING'},
                 {'status':'RESOLVED','reply_text':'x' * 5001}]:
        assert client.put(endpoint, headers=admin, json=body).status_code == 422
    assert client.put('/api/mobile/admin/feedback/999', headers=admin, json={'status':'PROCESSING'}).status_code == 404
    for query in ['page=0', 'page_size=101', 'status=INVALID']:
        assert client.get('/api/mobile/admin/feedback?' + query, headers=admin).status_code == 422
    assert client.post('/api/mobile/feedback', headers=auth(), json={'content':'      '}).status_code == 422
    assert client.get('/api/mobile/me/feedback', headers=auth()).json()['data'][0]['status'] == 'PENDING'


def test_exchange_fulfillment_receipt_admin_roles_and_owner_history(client):
    with client.sessions() as db:
        db.add(ExchangeItem(id=1, name='开发测试画材', energy_cost=50, stock=2))
        db.commit()
    body = {'request_id':'fulfill-receipt-test','item_id':1,'receiver_name':'开发测试',
            'receiver_phone':'100000','receiver_address':'开发测试地址'}
    record = client.post('/api/mobile/market/exchanges', headers=auth(), json=body).json()['data']['id']
    endpoint = f'/api/mobile/admin/exchanges/{record}'
    for headers in [auth(), auth(2, 'TEACHER')]:
        assert client.get('/api/mobile/admin/exchanges', headers=headers).status_code == 403
        assert client.put(endpoint, headers=headers, json={'status':'FULFILLED','tracking_no':'TEST'}).status_code == 403
    admin = auth(1, 'ADMIN')
    page = client.get('/api/mobile/admin/exchanges?status=REQUESTED&page_size=1', headers=admin).json()['data']
    assert page['total'] == 1 and page['items'][0]['receiver_address'] == body['receiver_address']
    assert client.put(endpoint, headers=admin, json={'status':'FULFILLED','tracking_no':'  '}).status_code == 422
    assert client.put(endpoint, headers=admin, json={'status':'CANCELLED','tracking_no':'TEST'}).status_code == 422
    receipt = {'status':'FULFILLED','tracking_no':' TEST-RECEIPT-001 ', 'handling_note':' 联调凭据，未实际寄送 '}
    assert client.put(endpoint, headers=admin, json=receipt).status_code == 200
    with client.sessions() as db:
        handled_at = db.get(EnergyExchange, record).handled_at
    assert client.put(endpoint, headers=admin, json=receipt).status_code == 200
    assert client.put(endpoint, headers=admin, json=receipt | {'tracking_no':'OTHER'}).status_code == 409
    assert client.put(endpoint, headers=admin, json={'status':'CANCELLED'}).status_code == 409
    owned = client.get('/api/mobile/me/exchanges', headers=auth()).json()['data'][0]
    assert owned['status'] == 'FULFILLED' and owned['tracking_no'] == 'TEST-RECEIPT-001'
    assert owned['handling_note'] == '联调凭据，未实际寄送' and owned['handled_at']
    assert 'receiver_address' not in owned and 'handled_by' not in owned
    assert client.get('/api/mobile/me/exchanges', headers=auth(4)).json()['data'] == []
    assert client.get('/api/mobile/admin/exchanges?status=REQUESTED', headers=admin).json()['data']['total'] == 0
    for query in ['page=0', 'page_size=101', 'status=INVALID']:
        assert client.get('/api/mobile/admin/exchanges?' + query, headers=admin).status_code == 422
    with client.sessions() as db:
        row = db.get(EnergyExchange, record)
        assert row.handled_by == 1 and row.handled_at == handled_at
        assert db.get(UserGrowth, 3).energy_value == 50 and db.get(ExchangeItem, 1).stock == 1
        assert db.query(GrowthEvent).filter_by(event_type='EXCHANGE_REFUND').count() == 0


def test_teacher_class_creation_forbidden_to_students(client):
    req = {"name": "传统工艺研习社", "grade": "小学三年级"}
    assert client.post("/api/mobile/teacher/classes", headers=auth(), json=req).status_code == 403
    result = client.post("/api/mobile/teacher/classes", headers=auth(2, "TEACHER"), json=req).json()["data"]
    assert len(result["invite_code"]) == 8


def test_teacher_student_assignment_review_roundtrip(client):
    assert client.post("/api/mobile/assignments/1/submit", headers=auth(), json={"content": "观察记录"}).status_code == 404
    for _ in range(2):
        assert client.post("/api/mobile/classes/join", headers=auth(), json={"invite_code": "test1234"}).status_code == 200
    with client.sessions() as db:
        assert db.query(ClassMember).count() == 1
    assignments = client.get("/api/mobile/me/assignments", headers=auth()).json()["data"]
    assert assignments[0]["title"] == "非遗观察"
    path = "/api/mobile/assignments/1/submit"
    assert client.post(path, headers=auth(), json={"content": "观察记录", "asset_id": 1}).status_code == 404
    sub = client.post(path, headers=auth(), json={"content": "观察记录"}).json()["data"]
    assert client.post(f'/api/teacher/submissions/{sub["id"]}/review', headers=auth(5, "TEACHER"),
                       json={"score": 90, "comment": "不应允许"}).status_code == 404
    assert client.post(f'/api/teacher/submissions/{sub["id"]}/review', headers=auth(2, "TEACHER"),
                       json={"score": 92, "comment": "观察细致"}).status_code == 200
    returned = client.get("/api/mobile/me/assignments", headers=auth()).json()["data"][0]["submission"]
    assert returned["score"] == 92 and returned["comment"] == "观察细致"
    assert client.post(path, headers=auth(), json={"content": "覆盖批改"}).status_code == 409


def test_expired_assignment_and_foreign_ownership(client):
    client.post("/api/mobile/classes/join", headers=auth(), json={"invite_code": "TEST1234"})
    with client.sessions() as db:
        db.get(Assignment, 1).deadline = datetime.utcnow() - timedelta(days=1)
        db.commit()
    assert client.post("/api/mobile/assignments/1/submit", headers=auth(), json={"content": "逾期"}).status_code == 409
    assert client.get("/api/mobile/me/assignments", headers=auth(4)).json()["data"] == []


def test_mobile_courses_use_real_ratings_and_grade_aliases(client):
    with client.sessions() as db:
        db.get(Course, 1).age_group = "小学低段"
        db.add(CourseRating(user_id=3, course_id=1, score=4))
        db.commit()
    result = client.get("/api/mobile/courses?age_group=PRIMARY_LOW").json()["data"]
    assert result["total"] == 1
    assert result["list"][0]["rating"] == 4
    assert result["list"][0]["progress_percent"] == 0


def test_canvas_design_requires_owned_image_and_persists_composition(client):
    request = {"cover_url": "/static/uploads/owned.png", "composition": [{"id": "pattern-1", "label": "云雷纹", "src": "/design/images/cloud.png", "x": .5, "y": .5, "scale": 1, "rotation": 0}], "title": "纹样设计", "render_style": "鎏金拓印"}
    assert client.post("/api/mobile/workshop/designs", headers=auth(), json=request).status_code == 404
    with client.sessions() as db:
        db.add(Asset(asset_type="IMAGE", object_key="uploads/owned.png", mime_type="image/png",
                     file_url=request["cover_url"], created_by=3))
        db.commit()
    result = client.post("/api/mobile/workshop/designs", headers=auth(), json=request).json()["data"]
    assert result["result"]["source"] == "user_canvas"
    restored = client.get('/api/ai/tasks/' + result["task_id"], headers=auth()).json()["data"]["input"]
    assert restored["composition"] == request["composition"]
    assert restored["render_style"] == request["render_style"]
    assert result["input"] == restored
    assert client.get('/api/ai/tasks/' + result["task_id"], headers=auth(4)).json()["code"] == 4040
    with client.sessions() as db:
        db.add(Asset(asset_type="IMAGE", object_key="uploads/owned2.png", mime_type="image/png",
                     file_url="/static/uploads/owned2.png", created_by=3))
        db.add(AiTask(task_id="f" * 32, user_id=3, tool_type="BRONZE", status="SUCCESS",
                      input_json={"title": "AI 纹样"}, result_summary_json={"source": "bronze_template"}))
        db.commit()
        before = db.query(AiTask).filter_by(user_id=3, tool_type="BRONZE").count()
    update = request | {"cover_url": "/static/uploads/owned2.png", "title": "更新后的纹样",
                        "render_style": "青铜氧化"}
    updated = client.put('/api/mobile/workshop/designs/' + result["task_id"], headers=auth(), json=update)
    assert updated.status_code == 200
    updated = updated.json()["data"]
    assert updated["task_id"] == result["task_id"]
    assert updated["input"]["title"] == "更新后的纹样"
    assert updated["input"]["render_style"] == "青铜氧化"
    assert updated["result"]["rendered_image_url"] == "/static/uploads/owned2.png"
    with client.sessions() as db:
        assert db.query(AiTask).filter_by(user_id=3, tool_type="BRONZE").count() == before
    assert client.put('/api/mobile/workshop/designs/' + result["task_id"], headers=auth(4),
                      json=update).status_code == 404
    assert client.put('/api/mobile/workshop/designs/' + "f" * 32, headers=auth(),
                      json=update).status_code == 404
    for field, value in [("x", -1), ("y", 2), ("scale", 3), ("rotation", 181)]:
        invalid = request | {"composition": [request["composition"][0] | {field: value}]}
        assert client.post("/api/mobile/workshop/designs", headers=auth(), json=invalid).status_code == 422
    assert client.post("/api/mobile/workshop/designs", headers=auth(), json=request | {"render_style": "unknown"}).status_code == 422


def test_shadow_task_generates_owned_assets_and_reports_actual_capabilities(client, monkeypatch, tmp_path):
    from app.api import ai_workshop
    from app.core import asset_generator
    from app.models.entities import AiTask
    monkeypatch.setattr(ai_workshop, "SessionLocal", client.sessions)
    monkeypatch.setattr(ai_workshop, "get_llm_client_and_config", lambda db: (None, None))
    monkeypatch.setattr(asset_generator, "STATIC_GENERATED_DIR", str(tmp_path))
    response = client.post('/api/ai/tasks', headers=auth(), json={
        "tool_type":"SHADOW_PUPPET", "input_payload":{
            "prompt":"花旦水袖", "role_type":"旦角", "color_palette":["#1256AB"]}})
    assert response.status_code == 200
    task_id = response.json()["data"]["task_id"]
    saved = client.get('/api/ai/tasks/' + task_id, headers=auth()).json()["data"]
    assert saved["status"] == "SUCCESS"
    result = saved["result"]
    assert result["generation_method"] == "local_template" and not result["model_available"]
    assert result["mesh_3d_url"] is None and result["color_palette"][0] == "#1256AB"
    assert "尚未经过实体装配" in result["description"]
    for key in ["colored_image_url", "line_art_url", "print_template_url"]:
        assert result[key].startswith('/static/generated/')
        assert (tmp_path / result[key].split('/')[-1]).is_file()
    colored = (tmp_path / result["colored_image_url"].split('/')[-1]).read_text()
    line = (tmp_path / result["line_art_url"].split('/')[-1]).read_text()
    assert '#1256AB' in colored and '#1256AB' not in line
    assert client.get('/api/ai/tasks/' + task_id, headers=auth(4)).json()["code"] == 4040
    latest = client.get('/api/ai/tasks/latest?tool_type=SHADOW_PUPPET', headers=auth()).json()["data"]
    assert latest["task_id"] == task_id and latest["result"] == result
    assert client.get('/api/mobile/me/summary', headers=auth()).json()["data"]["energy_value"] == 120
    assert client.get('/api/mobile/me/summary', headers=auth(4)).json()["data"]["energy_value"] == 0
    favorite_path = '/api/ai/tasks/' + task_id + '/favorite'
    assert not latest["collected"]
    for _ in range(2):
        assert client.post(favorite_path, headers=auth(), json={"collected":True}).json()["data"]["collected"]
    assert client.get('/api/ai/tasks/' + task_id, headers=auth()).json()["data"]["collected"]
    collections = client.get('/api/mobile/me/collections', headers=auth()).json()["data"]
    assert len(collections) == 1 and collections[0]["task_id"] == task_id
    assert collections[0]["type"] == "ASSET" and collections[0]["cover_url"] == result["colored_image_url"]
    assert client.post(favorite_path, headers=auth(4), json={"collected":True}).status_code == 404
    assert client.post('/api/mobile/collections/ASSET/' + str(collections[0]["id"]), headers=auth(4)).status_code == 404
    assert client.get('/api/mobile/me/collections', headers=auth(4)).json()["data"] == []
    for _ in range(2):
        assert not client.post(favorite_path, headers=auth(), json={"collected":False}).json()["data"]["collected"]
    assert client.get('/api/mobile/me/collections', headers=auth()).json()["data"] == []
    ai_workshop.execute_ai_inference(task_id, "SHADOW_PUPPET", 3)
    with client.sessions() as db:
        assert db.get(UserGrowth, 3).energy_value == 120
        assert db.query(GrowthEvent).filter_by(user_id=3, event_type="AI_CREATE").count() == 1
        assert db.query(AiTask).count() == 1


@pytest.mark.parametrize("role", ["生角","旦角","净角","丑角"])
def test_shadow_roles_and_face_styles_change_vector_geometry(client, monkeypatch, tmp_path, role):
    from xml.etree import ElementTree as ET
    from app.api import ai_workshop
    from app.core import asset_generator
    monkeypatch.setattr(ai_workshop, "SessionLocal", client.sessions)
    monkeypatch.setattr(ai_workshop, "get_llm_client_and_config", lambda db: (None, None))
    monkeypatch.setattr(asset_generator, "STATIC_GENERATED_DIR", str(tmp_path))
    shapes = []
    for style in ["CLASSIC","FLORAL","BOLD"]:
        created = client.post('/api/ai/tasks', headers=auth(), json={
            "tool_type":"SHADOW_PUPPET", "input_payload":{"prompt":"舞台角色", "role_type":role,
            "face_style":style, "color_palette":["#8B1A1A"]}}).json()["data"]
        saved = client.get('/api/ai/tasks/' + created["task_id"], headers=auth()).json()["data"]
        assert saved["status"] == "SUCCESS" and saved["result"]["role_type"] == role
        assert saved["result"]["face_style"] == style
        art = (tmp_path / saved["result"]["colored_image_url"].split('/')[-1]).read_text()
        tree = ET.fromstring(art)
        shapes.append(tuple(node.attrib.get("d") for node in tree.iter() if node.tag.endswith("path")))
        paper = (tmp_path / saved["result"]["print_template_url"].split('/')[-1]).read_text()
        assert "未验证实体装配" in paper and "直接将本文件发送至激光切割机" not in paper
        assert ET.fromstring(paper).tag.endswith("svg")
    assert len(set(shapes)) == 3
    if role in ["净角","丑角"]:
        expected = "PAINTED_JING" if role == "净角" else "COMIC_CHOU"
        assert asset_generator.detect_puppet_archetype("花旦", role) == expected
        assert "赶考书生" not in art


@pytest.mark.parametrize("payload", [
    {"prompt":"角色", "face_style":[]}, {"prompt":"角色", "face_style":"unknown"},
    {"prompt":""}, {"prompt":"x"*1001}, {"prompt":"角色", "color_palette":["bad"]},
])
def test_shadow_invalid_controls_do_not_create_tasks(client, payload):
    from app.models.entities import AiTask
    assert client.post('/api/ai/tasks', headers=auth(), json={"tool_type":"SHADOW_PUPPET", "input_payload":payload}).status_code == 422
    with client.sessions() as db:
        assert db.query(AiTask).count() == 0


def test_language_analysis_cannot_replace_selected_role_or_palette(client, monkeypatch, tmp_path):
    import json
    from types import SimpleNamespace
    from app.api import ai_workshop
    from app.core import asset_generator
    analysis = json.dumps({"title":"模型建议", "color_palette":["#0000FF"], "mentor_description":"文字建议"})
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=analysis))])
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response)))
    monkeypatch.setattr(ai_workshop, "SessionLocal", client.sessions)
    monkeypatch.setattr(ai_workshop, "get_llm_client_and_config", lambda db: (fake_client, {"model_name":"test-text-model"}))
    monkeypatch.setattr(asset_generator, "STATIC_GENERATED_DIR", str(tmp_path))
    created = client.post('/api/ai/tasks', headers=auth(), json={
        "tool_type":"SHADOW_PUPPET", "input_payload":{"prompt":"花旦", "role_type":"净角",
        "face_style":"BOLD", "color_palette":["#8B1A1A"]}}).json()["data"]
    result = client.get('/api/ai/tasks/' + created["task_id"], headers=auth()).json()["data"]["result"]
    assert result["role_type"] == "净角" and result["title"] == "模型建议" and result["llm_generated"]
    art = (tmp_path / result["colored_image_url"].split('/')[-1]).read_text()
    assert "#8B1A1A" in art and "#0000FF" not in art
    assert result["color_palette"][0] == "#8B1A1A" and result["generation_method"] == "local_template"


def test_unavailable_mesh_does_not_create_task_or_award_energy(client):
    from app.models.entities import AiTask
    response = client.post('/api/ai/tasks', headers=auth(), json={
        "tool_type":"MESH_3D", "input_payload":{"prompt":"皮影模型"}})
    assert response.status_code == 503 and "尚未配置" in response.json()["message"]
    with client.sessions() as db:
        assert db.query(AiTask).count() == 0 and db.query(GrowthEvent).count() == 0
        assert db.get(UserGrowth, 3).energy_value == 100


def test_legacy_shadow_claims_are_corrected_without_mutating_saved_results(client):
    from app.models.entities import AiTask
    original = {"role_type":"生角", "mesh_3d_url":"/static/models/tianjin_shadow_puppet.glb",
                "description":"可动骨骼三维模型", "colored_image_url":"/static/generated/original.svg"}
    with client.sessions() as db:
        db.add(AiTask(task_id="legacy-shadow", user_id=3, tool_type="SHADOW_PUPPET",
                      status="SUCCESS", progress=100, input_json={"color_palette":["#B85450"]}, result_summary_json=original))
        db.commit()
    for url in ['/api/ai/tasks/legacy-shadow', '/api/ai/tasks/latest?tool_type=SHADOW_PUPPET']:
        result = client.get(url, headers=auth()).json()["data"]["result"]
        assert result["mesh_3d_url"] is None and "三维模型生成尚未接入" in result["description"]
        assert result["colored_image_url"] == original["colored_image_url"]
        assert result["color_palette"][0] == "#B85450"
    with client.sessions() as db:
        assert db.query(AiTask).filter_by(task_id="legacy-shadow").one().result_summary_json == original


def test_bronze_workshop_only_counts_public_designs_and_authors(client):
    with client.sessions() as db:
        db.get(CommunityPost, 1).category = "BRONZE"
        db.get(CommunityPost, 2).category = "BRONZE"
        db.add_all([CommunityPost(id=3, user_id=4, title="另一件青铜作品", category="BRONZE", status="APPROVED"),
                    CommunityPost(id=4, user_id=3, title="皮影作品", category="SHADOW_PUPPET", status="APPROVED")])
        db.commit()
    result = client.get("/api/mobile/workshop/bronze").json()["data"]
    assert result["design_count"] == 2 and result["designer_count"] == 1
    assert {item["id"] for item in result["works"]} == {1, 3}
    assert all(item["nickname"] == "name-4" for item in result["works"])


def test_notices_respect_class_ownership_and_student_membership(client):
    payload = {"title": "明日非遗观察", "content": "请准备纸笔"}
    assert client.post("/api/mobile/teacher/classes/1/notices", headers=auth(5, "TEACHER"), json=payload).status_code == 404
    assert client.post("/api/mobile/teacher/classes/1/notices", headers=auth(2, "TEACHER"), json=payload).status_code == 200
    assert client.get("/api/mobile/classes/1/notices", headers=auth()).status_code == 404
    client.post("/api/mobile/classes/join", headers=auth(), json={"invite_code": "TEST1234"})
    assert client.get("/api/mobile/classes/1/notices", headers=auth()).json()["data"][0]["content"] == payload["content"]


def test_teacher_analytics_valid_progress_recent_quizzes_badges_and_scope(client, monkeypatch):
    from datetime import timezone, date
    from app.api import mobile_teacher
    from app.models.entities import CourseChapter, LearningProgress, Quiz, QuizQuestion, QuizAttempt, Badge, UserBadge, UserProfile
    from app.models.mobile import LearningDay
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            fixed = datetime(2026, 10, 17, 4, tzinfo=timezone.utc)
            return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)
    monkeypatch.setattr(mobile_teacher, "datetime", Clock)
    start = datetime(2026, 10, 10, 16)  # Shanghai Oct 11, inclusive.
    with client.sessions() as db:
        db.add_all([
            SysUser(id=6, username="disabled-analytics", nickname="停用学生", password_hash="unused", role_code="STUDENT", status="DISABLED"),
            SysUser(id=7, username="other-analytics", nickname="其他班学生", password_hash="unused", role_code="STUDENT"),
            UserProfile(user_id=2, school_name="蓟州区下营镇中心小学"),
            TeacherClass(id=2, teacher_id=5, name="其他教师", grade="初中", invite_code="OTHER777"),
            *[ClassMember(class_id=1, student_id=uid) for uid in (3, 3, 4, 2, 6)],
            ClassMember(class_id=2, student_id=7),
            CourseChapter(id=1, course_id=1, title="第一章"), CourseChapter(id=2, course_id=1, title="第二章"),
            CourseChapter(id=3, course_id=2, title="下架章节"),
            LearningProgress(user_id=3, course_id=1, chapter_id=1, completed=True),
            LearningProgress(user_id=3, course_id=1, chapter_id=1, completed=True),
            LearningProgress(user_id=3, course_id=1, chapter_id=3, completed=True),
            LearningProgress(user_id=3, course_id=2, chapter_id=3, completed=True),
            Quiz(id=1, course_id=1, title="当前测验"), Quiz(id=2, course_id=1, title="以前测验"),
            Quiz(id=3, course_id=2, title="下架测验"),
            QuizQuestion(quiz_id=1, content="问题", options_json=[], answer_json={}, score=100),
            QuizQuestion(quiz_id=2, content="问题", options_json=[], answer_json={}, score=20),
            QuizQuestion(quiz_id=3, content="问题", options_json=[], answer_json={}, score=100),
            QuizAttempt(user_id=3, quiz_id=1, score=80, answer_json={}, submitted_at=start),
            QuizAttempt(user_id=3, quiz_id=2, score=10, answer_json={}, submitted_at=start-timedelta(seconds=1)),
            QuizAttempt(user_id=3, quiz_id=3, score=100, answer_json={}, submitted_at=start),
            QuizAttempt(user_id=3, quiz_id=1, score=100, answer_json={}, submitted_at=datetime(2026,10,17,16)),
            Badge(id=1, code="BADGE_COURSE_BRONZE", name="青铜", description="专题课程", icon_url="/bronze.png"),
            Badge(id=2, code="BADGE_OTHER", name="其他", description="其他规则", icon_url="/other.png"),
            UserBadge(user_id=3, badge_id=1), UserBadge(user_id=3, badge_id=999),
            UserBadge(user_id=2, badge_id=2), UserBadge(user_id=6, badge_id=2), UserBadge(user_id=7, badge_id=2),
            LearningDay(user_id=3, day=date(2026,10,15)), LearningDay(user_id=3, day=date(2026,10,16)),
            LearningDay(user_id=4, day=date(2026,10,16)), LearningDay(user_id=7, day=date(2026,10,16)),
        ])
        db.commit()
    endpoint = "/api/mobile/teacher/classes/1/analytics"
    result = client.get(endpoint, headers=auth(2,"TEACHER"))
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["student_count"] == 2 and data["progress_student_count"] == 1
    assert data["mean_completion_rate"] == 50
    assert data["quiz_window_start"] == "2026-10-11" and data["quiz_window_end"] == "2026-10-17"
    student = next(s for s in data["students"] if s["id"]==3)
    assert student["completion_rate"] == 50 and student["quiz_accuracy_7d"] == 80
    assert student["quiz_accuracy"] == 75 and student["quiz_attempt_count_7d"] == 1
    unknown = next(s for s in data["students"] if s["id"]==4)
    assert unknown["completion_rate"] is None and unknown["quiz_accuracy_7d"] is None
    assert data["badge_total"] == data["unlocked_badge_types"] == 1 and data["badge_catalog_count"] == 2
    assert student["badge_count"] == 1 and [b["id"] for b in student["badges"]] == [1]
    assert [b["student_count"] for b in data["badge_catalog"]] == [1,0]
    assert data["learning_days_total"] == 3 and student["learning_days"] == 2
    classes = client.get("/api/teacher/classes", headers=auth(2,"TEACHER")).json()["data"]
    assert len(classes) == 1 and classes[0]["student_count"] == 2
    assert classes[0]["teacher_name"] == "name-2" and classes[0]["school"] == "蓟州区下营镇中心小学"
    assert classes[0]["completion"] == 50
    admin_classes = {c["id"]: c for c in client.get("/api/teacher/classes", headers=auth(1,"ADMIN")).json()["data"]}
    assert admin_classes[2]["teacher_name"] == "name-5" and admin_classes[2]["student_count"] == 1
    assert admin_classes[2]["school"] == "" and admin_classes[2]["completion"] is None
    assert client.get(endpoint, headers=auth()).status_code == 403
    assert client.get(endpoint, headers=auth(5,"TEACHER")).status_code == 404
    assert client.get("/api/mobile/teacher/classes/2/analytics", headers=auth(2,"TEACHER")).status_code == 404
    assert client.get(endpoint, headers=auth(1,"ADMIN")).status_code == 200
    with client.sessions() as db:
        assert db.get(UserGrowth,3).energy_value == 100 and db.query(UserBadge).count() == 5


def test_teacher_analytics_empty_unknown_and_inactive_class(client):
    endpoint = "/api/mobile/teacher/classes/1/analytics"
    assert client.get(endpoint).status_code == 401
    data = client.get(endpoint, headers=auth(2,"TEACHER")).json()["data"]
    assert data["students"] == [] and data["badge_catalog"] == []
    assert data["mean_completion_rate"] is None and data["badge_total"] == 0
    assert data["student_count"] == data["progress_student_count"] == data["learning_days_total"] == 0
    with client.sessions() as db:
        db.get(TeacherClass,1).status="INACTIVE"
        db.commit()
    assert client.get(endpoint, headers=auth(2,"TEACHER")).status_code == 404


def test_attendance_rejects_stale_shanghai_day_without_overwriting(client, monkeypatch):
    from app.api import mobile_teacher
    from app.models.mobile import ClassAttendance
    client.post("/api/mobile/classes/join", headers=auth(), json={"invite_code":"TEST1234"})
    monkeypatch.setattr(mobile_teacher,"today",lambda:"2026-10-17")
    endpoint="/api/mobile/teacher/classes/1/attendance"
    body={"day":"2026-10-16","records":[{"student_id":3,"status":"PRESENT"}]}
    assert client.put(endpoint, headers=auth(2,"TEACHER"), json=body).status_code == 409
    with client.sessions() as db:
        assert db.query(ClassAttendance).count() == 0
    body["day"]="2026-10-17"
    assert client.put(endpoint, headers=auth(2,"TEACHER"), json=body).status_code == 200
    body["day"]="2026-10-16";body["records"][0]["status"]="ABSENT"
    assert client.put(endpoint, headers=auth(2,"TEACHER"), json=body).status_code == 409
    with client.sessions() as db:
        assert db.get(ClassAttendance,(1,3,"2026-10-17")).status == "PRESENT"


def test_attendance_validates_members_and_overview_uses_records(client):
    client.post("/api/mobile/classes/join", headers=auth(), json={"invite_code": "TEST1234"})
    endpoint = "/api/mobile/teacher/classes/1/attendance"
    assert client.put(endpoint, headers=auth(2, "TEACHER"), json={"records": [{"student_id": 4, "status": "PRESENT"}]}).status_code == 422
    assert client.put(endpoint, headers=auth(2, "TEACHER"), json={"records": [{"student_id": 3, "status": "PRESENT"}]}).status_code == 200
    result = client.get("/api/mobile/teacher/overview", headers=auth(2, "TEACHER")).json()["data"]
    assert result["student_count"] == 1 and result["attendance_rate"] == 100
    students = client.get("/api/mobile/teacher/classes/1/students", headers=auth(2, "TEACHER")).json()["data"]
    assert students[0]["attendance"] == "PRESENT"
    assert client.get("/api/mobile/teacher/classes/1/students", headers=auth(5, "TEACHER")).status_code == 404


def test_teacher_overview_scopes_current_members_and_deduplicates_pairs(client):
    from datetime import timezone, time
    from zoneinfo import ZoneInfo
    from app.models.mobile import ClassAttendance, ClassSession, ClassMessage, LessonPlanRecord
    from app.models.entities import CourseChapter, LearningProgress
    local_day = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    start = datetime.combine(local_day, time.min, ZoneInfo("Asia/Shanghai")).astimezone(timezone.utc).replace(tzinfo=None)
    with client.sessions() as db:
        db.add(SysUser(id=6, username="inactive", nickname="停用学生", password_hash="unused", role_code="STUDENT", status="INACTIVE"))
        db.add(SysUser(id=7, username="former", nickname="退出学生", password_hash="unused", role_code="STUDENT"))
        db.add_all([
            TeacherClass(id=2, teacher_id=2, name="第二班", grade="小学三年级"),
            TeacherClass(id=3, teacher_id=5, name="其他教师班", grade="小学三年级"),
            TeacherClass(id=4, teacher_id=2, name="停用班", grade="小学三年级", status="INACTIVE"),
            ClassMember(class_id=1, student_id=3), ClassMember(class_id=1, student_id=3),
            ClassMember(class_id=2, student_id=3), ClassMember(class_id=2, student_id=4),
            ClassMember(class_id=1, student_id=6), ClassMember(class_id=1, student_id=7, status="LEFT"),
            ClassMember(class_id=1, student_id=5), ClassMember(class_id=3, student_id=4),
            Assignment(id=2, class_id=2, teacher_id=2, title="第二班作业", description="观察", deadline=datetime.utcnow()+timedelta(hours=1)),
            Assignment(id=3, class_id=2, teacher_id=2, title="草稿", description="草稿", deadline=datetime.utcnow(), status="DRAFT"),
            Assignment(id=4, class_id=3, teacher_id=5, title="他班作业", description="观察", deadline=datetime.utcnow()),
            Assignment(id=5, class_id=4, teacher_id=2, title="停用班作业", description="观察", deadline=datetime.utcnow()),
            AssignmentSubmission(id=1, assignment_id=1, student_id=3),
            AssignmentSubmission(id=2, assignment_id=1, student_id=3),
            AssignmentSubmission(id=3, assignment_id=1, student_id=4),
            AssignmentSubmission(id=4, assignment_id=2, student_id=3),
            AssignmentSubmission(id=5, assignment_id=2, student_id=4, status="DRAFT"),
            AssignmentSubmission(id=6, assignment_id=2, student_id=6),
            AssignmentSubmission(id=7, assignment_id=3, student_id=3),
            AssignmentSubmission(id=8, assignment_id=4, student_id=3),
            ClassAttendance(class_id=1, student_id=3, day=local_day.isoformat(), status="PRESENT", recorded_by=2),
            ClassAttendance(class_id=2, student_id=3, day=local_day.isoformat(), status="PRESENT", recorded_by=2),
            ClassAttendance(class_id=2, student_id=4, day=local_day.isoformat(), status="LEAVE", recorded_by=2),
            ClassAttendance(class_id=1, student_id=4, day=local_day.isoformat(), status="ABSENT", recorded_by=2),
            ClassAttendance(class_id=1, student_id=6, day=local_day.isoformat(), status="PRESENT", recorded_by=2),
            ClassSession(id=1, class_id=1, host_id=2, title="课堂一"),
            ClassSession(id=2, class_id=2, host_id=2, title="课堂二", status="ENDED"),
            ClassSession(id=3, class_id=3, host_id=5, title="他班课堂"),
            CourseChapter(id=1, course_id=1, seq=1, title="完整章节"),
            LearningProgress(user_id=2, course_id=1, chapter_id=1, completed=True),
            AssignmentReview(submission_id=1, teacher_id=2, score=90),
            LessonPlanRecord(teacher_id=2, title="今日教案", grade="小学", topic="皮影", duration_minutes=45, content_json={}, source="本地课程模板", created_at=start),
            LessonPlanRecord(teacher_id=2, title="昨日教案", grade="小学", topic="皮影", duration_minutes=45, content_json={}, source="本地课程模板", created_at=start-timedelta(seconds=1)),
        ])
        for session_id, user_id, kind in [(1,3,"HAND"),(1,3,"HAND"),(2,4,"CHAT"),(1,2,"CHAT"),(1,4,"HAND"),(1,6,"HAND"),(3,3,"HAND")]:
            db.add(ClassMessage(session_id=session_id,user_id=user_id,type=kind,content="测试互动",created_at=start+timedelta(hours=1)))
        db.add(ClassMessage(session_id=1,user_id=3,type="HAND",content="昨日举手",created_at=start-timedelta(seconds=1)))
        db.add(ClassMessage(session_id=1,user_id=3,type="HAND",content="明日举手",created_at=start+timedelta(days=1)))
        db.commit()
    data=client.get("/api/mobile/teacher/overview",headers=auth(2,"TEACHER")).json()["data"]
    assert data["class_count"] == 2 and data["student_count"] == 2
    assert data["attendance_expected"] == data["attendance_recorded"] == 3
    assert data["attendance_present"] == 2 and data["attendance_leave"] == 1
    assert data["attendance_absent"] == data["attendance_unrecorded"] == 0 and data["attendance_rate"] == 66.7
    assert data["assignment_count"] == 2 and data["submission_expected"] == 3
    assert data["submission_count"] == 2 and data["submission_pending"] == 1 and data["submission_rate"] == 66.7
    assert data["next_assignment_deadline"] and data["session_count"] == 2 and data["active_session_count"] == 1
    assert data["interaction_count"] == 6 and data["hand_raiser_count"] == 1
    assert data["activity_participant_count"] == 2 and data["activity_score"] == 100
    assert data["lesson_plan_count"] == 2 and data["lesson_plan_today_count"] == 1 and data["day"] == local_day.isoformat()
    assert len(data["achievements"]) == 4 and all(a["completed"] for a in data["achievements"])
    roster=client.get("/api/mobile/teacher/classes/1/students",headers=auth(2,"TEACHER")).json()["data"]
    assert [student["id"] for student in roster] == [3]
    assert client.put("/api/mobile/teacher/classes/1/attendance",headers=auth(2,"TEACHER"),
        json={"records":[{"student_id":6,"status":"PRESENT"}]}).status_code == 422
    other=client.get("/api/mobile/teacher/overview",headers=auth(5,"TEACHER")).json()["data"]
    assert other["class_count"] == other["student_count"] == 1
    assert other["interaction_count"] == 1 and other["activity_participant_count"] == 0
    assert not any(a["completed"] for a in other["achievements"] if a["code"] != "ACTIVE_STUDENT")


def test_teacher_overview_empty_metrics_are_unknown_and_achievements_do_not_award(client):
    from app.models.entities import UserBadge
    endpoint="/api/mobile/teacher/overview"
    assert client.get(endpoint,headers=auth()).status_code == 403
    data=client.get(endpoint,headers=auth(5,"TEACHER")).json()["data"]
    assert data["class_count"] == data["student_count"] == data["attendance_expected"] == 0
    assert data["attendance_rate"] is data["submission_rate"] is data["activity_score"] is None
    assert data["next_assignment_deadline"] is None
    assert len(data["achievements"]) == 4 and not any(a["completed"] for a in data["achievements"])
    assert all(a["description"] and a["path"] and a["target"] == 1 for a in data["achievements"])
    client.get(endpoint,headers=auth(5,"TEACHER"))
    with client.sessions() as db:
        assert db.query(UserBadge).filter_by(user_id=5).count() == 0
        assert db.get(UserGrowth,3).energy_value == 100


def test_ballad_returns_template_and_never_mislabels_rain_as_generated_audio(client, monkeypatch, tmp_path):
    from app.api import ai_workshop
    from app.core import asset_generator
    from app.models.entities import AiTask
    monkeypatch.setattr(ai_workshop,"SessionLocal",client.sessions)
    monkeypatch.setattr(ai_workshop,"get_llm_client_and_config",lambda db:(None,None))
    monkeypatch.setattr(asset_generator,"STATIC_GENERATED_DIR",str(tmp_path))
    response=client.post("/api/ai/tasks",headers=auth(),json={"tool_type":"BALLAD","input_payload":{"prompt":"运河风光"}})
    assert response.status_code == 200
    task_id=response.json()["data"]["task_id"]
    saved=client.get("/api/ai/tasks/"+task_id,headers=auth()).json()["data"]
    assert saved["status"] == "SUCCESS"
    result=saved["result"]
    assert result["audio_url"] is None and not result["audio_available"] and not result["custom_melody_available"]
    assert result["generation_method"] == "local_sheet_template" and "固定示例音符" in result["description"]
    assert (tmp_path/result["sheet_music_url"].split("/")[-1]).is_file()
    with client.sessions() as db:
        db.add(AiTask(task_id="legacy-ballad",user_id=3,tool_type="BALLAD",status="SUCCESS",input_json={},result_summary_json={
            "audio_url":"https://actions.google.com/sounds/v1/water/rain_heavy.ogg","description":"已完成配曲"}))
        db.commit()
    for path in ["/api/ai/tasks/legacy-ballad","/api/ai/tasks/latest?tool_type=BALLAD"]:
        result=client.get(path,headers=auth()).json()["data"]["result"]
        assert result["audio_url"] is None and not result["audio_available"] and "尚未接入" in result["description"]
    with client.sessions() as db:
        assert db.query(AiTask).filter_by(task_id="legacy-ballad").one().result_summary_json["audio_url"].endswith("rain_heavy.ogg")


def test_lesson_history_is_private_and_exports_actual_stored_content(client):
    import io
    import zipfile
    result = client.post("/api/mobile/teacher/lesson-plans", headers=auth(2, "TEACHER"),
                         json={"grade": "小学三年级", "topic": "杨柳青年画", "duration_minutes": 45}).json()["data"]
    assert result["source"] == "本地课程模板"
    endpoint = '/api/mobile/teacher/lesson-plans/' + str(result["id"])
    assert client.get(endpoint, headers=auth(5, "TEACHER")).status_code == 404
    assert client.get(endpoint + '/pptx', headers=auth()).status_code == 403
    response = client.get(endpoint + '/pptx', headers=auth(2, "TEACHER"))
    assert response.status_code == 200 and response.content.startswith(b'PK')
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        slides = [archive.read(name).decode() for name in archive.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')]
    assert any('杨柳青年画' in slide for slide in slides)
    assert any('教学目标' in slide for slide in slides)


def test_classroom_discussion_auth_live_flow_and_end_state(client):
    result = client.post("/api/mobile/teacher/classes/1/sessions", headers=auth(2, "TEACHER"),
                         json={"title": "皮影观察课堂"}).json()["data"]
    endpoint = '/api/mobile/classroom/' + str(result["id"])
    assert client.get(endpoint, headers=auth()).status_code == 404
    client.post("/api/mobile/classes/join", headers=auth(), json={"invite_code": "TEST1234"})
    assert client.post(endpoint + '/messages', headers=auth(), json={"type": "HAND", "content": "我想提问"}).status_code == 200
    room = client.get(endpoint, headers=auth(2, "TEACHER")).json()["data"]
    assert room["messages"][0]["nickname"] == 'name-3'
    assert client.get(endpoint, headers=auth(5, "TEACHER")).status_code == 404
    assert client.post(endpoint + '/end', headers=auth(2, "TEACHER")).status_code == 200
    assert client.post(endpoint + '/messages', headers=auth(), json={"content": "课后消息"}).status_code == 409


def test_order_retry_reuses_original_order_and_stock(client):
    from app.models.entities import Product, ProductSku, OrderMain
    with client.sessions() as db:
        db.add(Product(id=1, name="文创礼盒", cover_url="/x.png", fund_rate_percent=10))
        db.add(ProductSku(id=1, product_id=1, name="标准装", sku_code="idempotent-test", price_cents=1000, stock=5))
        db.commit()
    body = {"request_id": "same-order-123", "items": [{"product_id": 1, "sku_id": 1, "quantity": 1}],
            "receiver_name": "开发测试", "receiver_phone": "100000", "receiver_address": "开发测试地址"}
    first = client.post('/api/mall/orders', headers=auth(), json=body).json()["data"]
    second = client.post('/api/mall/orders', headers=auth(), json=body).json()["data"]
    assert first["order_no"] == second["order_no"]
    with client.sessions() as db:
        assert db.query(OrderMain).count() == 1 and db.get(ProductSku, 1).stock == 4
    body["items"][0]["quantity"] = 2
    assert client.post('/api/mall/orders', headers=auth(), json=body).status_code == 409


def test_exchange_idempotent_debit_and_admin_refund(client):
    with client.sessions() as db:
        db.get(UserGrowth, 3).energy_value = 1000
        db.add(ExchangeItem(id=1, name="水彩画材", energy_cost=500, stock=2))
        db.commit()
    body = {"request_id": "same-reward-123", "item_id": 1, "receiver_name": "开发测试",
            "receiver_phone": "100000", "receiver_address": "开发测试地址"}
    first = client.post('/api/mobile/market/exchanges', headers=auth(), json=body).json()["data"]
    second = client.post('/api/mobile/market/exchanges', headers=auth(), json=body).json()["data"]
    assert first["id"] == second["id"]
    with client.sessions() as db:
        assert db.get(UserGrowth, 3).energy_value == 500 and db.get(ExchangeItem, 1).stock == 1
        assert db.query(EnergyExchange).count() == 1
    endpoint = '/api/mobile/admin/exchanges/' + str(first["id"])
    assert client.put(endpoint, headers=auth(), json={"status": "CANCELLED"}).status_code == 403
    for _ in range(2):
        assert client.put(endpoint, headers=auth(1, "ADMIN"), json={"status": "CANCELLED"}).status_code == 200
    with client.sessions() as db:
        assert db.get(UserGrowth, 3).energy_value == 1000 and db.get(ExchangeItem, 1).stock == 2


def test_exchange_insufficient_energy_and_out_of_stock(client):
    with client.sessions() as db:
        db.add(ExchangeItem(id=1, name="画材", energy_cost=500, stock=1))
        db.add(ExchangeItem(id=2, name="缺货", energy_cost=50, stock=0))
        db.commit()
    body = {"request_id": "not-enough-123", "item_id": 1, "receiver_name": "测试",
            "receiver_phone": "100000", "receiver_address": "测试地址"}
    assert client.post('/api/mobile/market/exchanges', headers=auth(), json=body).status_code == 409
    body["item_id"] = 2
    assert client.post('/api/mobile/market/exchanges', headers=auth(), json=body).status_code == 409
    with client.sessions() as db:
        assert db.get(UserGrowth, 3).energy_value == 100 and db.query(EnergyExchange).count() == 0


def test_walking_ownership_time_bounds_and_repeated_finish(client):
    first = client.post('/api/mobile/walks', headers=auth()).json()["data"]
    second = client.post('/api/mobile/walks', headers=auth()).json()["data"]
    assert first["id"] == second["id"]
    endpoint = '/api/mobile/walks/' + str(first["id"])
    assert client.put(endpoint, headers=auth(4), json={"active_seconds": 100}).status_code == 404
    assert client.put(endpoint, headers=auth(), json={"active_seconds": 10, "latitude": 100, "longitude": 1}).status_code == 422
    with client.sessions() as db:
        db.get(WalkSession, first["id"]).started_at = datetime.utcnow() - timedelta(seconds=120)
        db.commit()
    reported = client.put(endpoint, headers=auth(), json={"active_seconds": 10000, "completed": True}).json()["data"]
    assert 120 <= reported["active_seconds"] <= 123 and reported["status"] == "COMPLETED"
    repeated = client.put(endpoint, headers=auth(), json={"active_seconds": 20000, "completed": True}).json()["data"]
    assert repeated["active_seconds"] == reported["active_seconds"]


def test_contest_assignment_creation_and_visibility(client):
    body = {
        "class_id": 1,
        "title": "班级皮影创作PK对抗赛",
        "type": "CONTEST",
        "tool_type": "SHADOW_PUPPET",
        "deadline_days": 5,
        "description": "以非遗皮影为主题，开展班级间创意角色对抗赛"
    }
    res = client.post('/api/teacher/assignments', headers=auth(2, role='TEACHER'), json=body)
    assert res.status_code == 200, res.text
    assignment_id = res.json()["data"]["id"]

    # Student joins class and checks assignment list
    join_res = client.post("/api/mobile/classes/join", headers=auth(3, role='STUDENT'), json={"invite_code": "TEST1234"})
    assert join_res.status_code == 200

    student_res = client.get('/api/mobile/me/assignments', headers=auth(3, role='STUDENT'))
    assert student_res.status_code == 200
    items = student_res.json()["data"]
    contest_item = next((item for item in items if item["id"] == assignment_id), None)
    assert contest_item is not None
    assert contest_item["type"] == "CONTEST"
    assert "对抗赛" in contest_item["title"]


@pytest.mark.parametrize("tool", ["EMBROIDERY", "LACQUER"])
@pytest.mark.parametrize("pattern", ["FLORAL", "GEOMETRIC", "AUSPICIOUS"])
def test_lacquer_owned_reference_local_pattern_and_actual_capabilities(client, monkeypatch, tmp_path, tool, pattern):
    import base64
    from xml.etree import ElementTree
    from app.api import ai_workshop
    from app.core import asset_generator, files
    from app.models.entities import AiTask
    uploads = tmp_path / 'uploads'
    uploads.mkdir()
    monkeypatch.setattr(ai_workshop, 'SessionLocal', client.sessions)
    monkeypatch.setattr(ai_workshop, 'get_llm_client_and_config', lambda db: (None, None))
    monkeypatch.setattr(ai_workshop, 'STATIC_UPLOADS_DIR', str(uploads))
    monkeypatch.setattr(asset_generator, 'STATIC_GENERATED_DIR', str(tmp_path))
    monkeypatch.setattr(files, 'STATIC_DIR', tmp_path)
    png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
    upload = client.post('/api/ai/assets/upload', headers=auth(), files={'file':('reference.png',png,'image/png')})
    assert upload.status_code == 200
    reference = upload.json()['data']['file_url']
    assert (uploads / reference.split('/')[-1]).read_bytes() == png
    response = client.post('/api/ai/tasks', headers=auth(), json={
        'tool_type':tool, 'input_payload':{'prompt':'福字纹样' if pattern == 'AUSPICIOUS' else '喜上眉梢的花鸟', 'local_pattern':pattern,
                                          'color_palette':['#1256AB','#D4AF37','#2D5A4A','#1A1817','#F7F4ED'],
                                          'style':'花鸟LoRA', 'sketch_url':reference}})
    assert response.status_code == 200, response.text
    task_id = response.json()['data']['task_id']
    saved = client.get('/api/ai/tasks/' + task_id, headers=auth()).json()['data']
    assert saved['status'] == 'SUCCESS'
    result = saved['result']
    assert result['local_pattern'] == pattern and result['color_palette'][0] == '#1256AB'
    assert result['generation_method'] == 'local_template'
    assert result['reference_sketch_url'] == reference
    assert result['completed_sketch_url'] is None and result['print_template_url'] is None
    assert not any(result[k] for k in ['model_available','sketch_redraw_available','lora_available','lora_applied'])
    assert '未进行轮廓识别或草图重绘' in result['description']
    svg = (tmp_path / result['colored_image_url'].split('/')[-1]).read_text()
    root = ElementTree.fromstring(svg)
    assert '#1256AB' in svg and '本地二维纹样参考' in ''.join(root.itertext())
    paths = root.findall('.//{http://www.w3.org/2000/svg}path')
    if pattern == 'GEOMETRIC':
        assert len(paths) == 18
    elif pattern == 'AUSPICIOUS':
        assert '福' in ''.join(root.itertext()) and len(paths) == 1
    else:
        assert any('Q' in path.attrib['d'] for path in paths)
    assert client.post('/api/ai/tasks/' + task_id + '/favorite', headers=auth(), json={'collected':True}).json()['data']['collected']
    assert client.post('/api/ai/tasks/' + task_id + '/favorite', headers=auth(4), json={'collected':True}).status_code == 404
    ai_workshop.execute_ai_inference(task_id, tool, 3)
    with client.sessions() as db:
        assert db.get(UserGrowth,3).energy_value == 120
        assert db.query(GrowthEvent).filter_by(user_id=3,event_type='AI_CREATE').count() == 1
        assert db.get(AiTask,task_id).input_json['sketch_url'] == reference


@pytest.mark.parametrize('tool', ['EMBROIDERY','LACQUER'])
def test_lacquer_legacy_claims_are_corrected_without_rewriting_saved_results(client, tool):
    from app.models.entities import AiTask
    original = {'title':'旧创作','completed_sketch_url':'/static/old.svg','print_template_url':'/static/old.svg',
                'description':'精准提取光谱并完成草图重绘','lora_applied':True,'model_available':True,'llm_generated':True}
    with client.sessions() as db:
        db.add(AiTask(task_id='legacy-' + tool,user_id=3,tool_type=tool,status='SUCCESS',input_json={},result_summary_json=original))
        db.commit()
    for path in ['/api/ai/tasks/legacy-' + tool,'/api/ai/tasks/latest?tool_type=' + tool]:
        result = client.get(path, headers=auth()).json()['data']['result']
        assert result['completed_sketch_url'] is None and result['print_template_url'] is None
        assert not result['lora_applied'] and not result['sketch_redraw_available'] and not result['model_available']
        assert '实物材料色号' in result['description']
    with client.sessions() as db:
        assert db.get(AiTask,'legacy-' + tool).result_summary_json == original


@pytest.mark.parametrize('payload', [
    {'prompt':''}, {'prompt':None}, {'prompt':'a'*1001}, {'prompt':'纹样','local_pattern':[]},
    {'prompt':'纹样','local_pattern':'UNKNOWN'}, {'prompt':'纹样','color_palette':['bad']},
    {'prompt':'纹样','sketch_url':[]}, {'prompt':'纹样','sketch_url':'https://example.com/private.png'},
])
def test_lacquer_invalid_controls_do_not_create_task_or_reward(client, payload):
    from app.models.entities import AiTask
    response = client.post('/api/ai/tasks',headers=auth(),json={'tool_type':'EMBROIDERY','input_payload':payload})
    assert response.status_code == 422
    with client.sessions() as db:
        assert db.query(AiTask).count() == 0 and db.query(GrowthEvent).count() == 0


def test_lacquer_rejects_other_users_or_non_image_references(client):
    from app.models.entities import AiTask
    with client.sessions() as db:
        db.add_all([Asset(asset_type='IMAGE',object_key='uploads/other.png',file_url='/static/uploads/other.png',mime_type='image/png',created_by=4),
                    Asset(asset_type='MEDIA',object_key='uploads/clip.mp4',file_url='/static/uploads/clip.mp4',mime_type='video/mp4',created_by=3)])
        db.commit()
    for url in ['/static/uploads/other.png','/static/uploads/clip.mp4']:
        response = client.post('/api/ai/tasks',headers=auth(),json={'tool_type':'EMBROIDERY','input_payload':{'prompt':'纹样','sketch_url':url}})
        assert response.status_code == 404
    with client.sessions() as db:
        assert db.query(AiTask).count() == 0 and db.query(GrowthEvent).count() == 0




def test_class_contest_full_flow_locks_scores_and_hides_peer_data(client):
    from app.models.entities import Contest, ContestEntry
    with client.sessions() as db:
        db.add_all([
            TeacherClass(id=2, teacher_id=2, name="二班", grade="小学三年级", invite_code="TEST5678"),
            ClassMember(class_id=1, student_id=3),
            ClassMember(class_id=2, student_id=4),
            SysUser(id=6, username="user-6", nickname="name-6",
                    password_hash="x", role_code="STUDENT", token_version=0),
            ClassMember(class_id=1, student_id=6),
        ])
        db.commit()

    created = client.post("/api/teacher/contests", headers=auth(2, "TEACHER"), json={
        "title": "纹样对抗赛", "description": "完成青铜纹样创作",
        "tool_type": "BRONZE_PATTERN", "home_class_id": 1, "away_class_id": 2,
        "round_no": 1, "scoring_mode": "TOTAL", "deadline_days": 3,
        "home_student_ids": [3], "away_student_ids": [4],
    })
    assert created.status_code == 200
    contest = created.json()["data"]
    contest_id, home_assignment = contest["id"], contest["home_assignment_id"]
    away_assignment = contest["away_assignment_id"]
    assert contest["status"] == "OPEN"

    expanded = client.put(f"/api/teacher/contests/{contest_id}/entries",
                          headers=auth(2, "TEACHER"),
                          json={"home_student_ids": [3, 6], "away_student_ids": [4]})
    assert expanded.status_code == 200
    assert expanded.json()["data"]["classes"][0]["participant_count"] == 2
    trimmed = client.put(f"/api/teacher/contests/{contest_id}/entries",
                         headers=auth(2, "TEACHER"),
                         json={"home_student_ids": [3], "away_student_ids": [4]})
    assert trimmed.status_code == 200
    assert trimmed.json()["data"]["classes"][0]["participant_count"] == 1
    duplicate = client.put(f"/api/teacher/contests/{contest_id}/entries",
                           headers=auth(2, "TEACHER"),
                           json={"home_student_ids": [3, 3], "away_student_ids": [4]})
    assert duplicate.status_code == 409

    home_list = client.get("/api/mobile/me/assignments", headers=auth()).json()["data"]
    assert any(row["id"] == home_assignment and row["contest"]["id"] == contest_id for row in home_list)
    outsider_list = client.get("/api/mobile/me/assignments", headers=auth(6)).json()["data"]
    assert all(row["id"] != home_assignment for row in outsider_list)

    submitted = client.post(f"/api/mobile/assignments/{home_assignment}/submit",
                            headers=auth(), json={"content": "一班作品"})
    assert submitted.status_code == 200
    submitted = client.post(f"/api/mobile/assignments/{away_assignment}/submit",
                            headers=auth(4), json={"content": "二班作品"})
    assert submitted.status_code == 200
    denied = client.post(f"/api/mobile/assignments/{home_assignment}/submit",
                         headers=auth(6), json={"content": "非参赛者"})
    assert denied.status_code == 404

    removed = client.put(f"/api/teacher/contests/{contest_id}/entries",
                         headers=auth(2, "TEACHER"), json={"home_student_ids": []})
    assert removed.status_code == 409

    home_subs = client.get(f"/api/teacher/assignments/{home_assignment}/submissions",
                           headers=auth(2, "TEACHER")).json()["data"]
    away_subs = client.get(f"/api/teacher/assignments/{away_assignment}/submissions",
                           headers=auth(2, "TEACHER")).json()["data"]
    assert client.post(f"/api/teacher/submissions/{home_subs[0]['id']}/review",
                       headers=auth(2, "TEACHER"),
                       json={"score": 88, "comment": "纹样完整"}).status_code == 200
    assert client.post(f"/api/teacher/submissions/{away_subs[0]['id']}/review",
                       headers=auth(2, "TEACHER"),
                       json={"score": 92, "comment": "构图更好"}).status_code == 200

    before = client.get(f"/api/mobile/me/contests/{contest_id}", headers=auth()).json()["data"]
    assert before["published"] is False and before["my_entry"]["score"] is None
    hidden_list = client.get("/api/mobile/me/assignments", headers=auth()).json()["data"]
    hidden_row = next(row for row in hidden_list if row["id"] == home_assignment)
    assert hidden_row["submission"]["score"] is None and hidden_row["submission"]["comment"] is None
    assert "entries" not in before and "student_name" not in str(before)

    published = client.post(f"/api/teacher/contests/{contest_id}/status",
                            headers=auth(2, "TEACHER"), json={"status": "PUBLISHED"})
    assert published.status_code == 200
    detail = published.json()["data"]
    assert detail["status"] == "PUBLISHED"
    assert detail["winner_class_id"] == 2
    assert detail["classes"][0]["scored_count"] == 1

    after = client.get(f"/api/mobile/me/contests/{contest_id}", headers=auth()).json()["data"]
    assert after["published"] is True
    assert after["my_entry"]["score"] == 88 and after["my_entry"]["rank"] == 1
    assert after["winner_class_id"] == 2
    assert "entries" not in after and "name-4" not in str(after)

    locked_review = client.post(f"/api/teacher/submissions/{home_subs[0]['id']}/review",
                                headers=auth(2, "TEACHER"),
                                json={"score": 99, "comment": "改分"})
    assert locked_review.status_code == 409
    locked_submit = client.post(f"/api/mobile/assignments/{home_assignment}/submit",
                                headers=auth(), json={"content": "重新提交"})
    assert locked_submit.status_code == 409
    locked_roster = client.put(f"/api/teacher/contests/{contest_id}/entries",
                               headers=auth(2, "TEACHER"),
                               json={"home_student_ids": [3, 6]})
    assert locked_roster.status_code == 409

    assert client.get(f"/api/teacher/contests/{contest_id}",
                      headers=auth(5, "TEACHER")).status_code == 404
    assert client.get(f"/api/teacher/contests/{contest_id}", headers=auth()).status_code == 403
    with client.sessions() as db:
        assert db.query(ContestEntry).filter_by(contest_id=contest_id).count() == 2
        assert db.get(Contest, contest_id).result_json["winner_class_id"] == 2


def test_admin_catalog_manages_badges_products_and_exchange_items(client):
    from app.models.entities import Badge, UserBadge, Product, ProductSku
    from app.models.mobile import ExchangeItem
    with client.sessions() as db:
        db.add_all([
            Badge(id=9, code="BADGE_LEGACY", name="既有徽章", description="已有持有人",
                  icon_url="/static/legacy.png", condition_json={"type": "MANUAL"}),
            UserBadge(user_id=3, badge_id=9),
        ])
        db.commit()

    assert client.get("/api/admin/catalog/badges", headers=auth()).status_code == 403
    listed = client.get("/api/admin/catalog/badges", headers=auth(1, "ADMIN")).json()["data"]
    assert listed[0]["holders"] == 1

    created_badge = client.post("/api/admin/catalog/badges", headers=auth(1, "ADMIN"), json={
        "code": "BADGE_NEW", "name": "新徽章", "description": "新条件",
        "icon_url": "/static/new.png", "condition_json": {"type": "MANUAL"},
    })
    assert created_badge.status_code == 200
    badge_id = created_badge.json()["data"]["id"]
    assert client.delete(f"/api/admin/catalog/badges/{badge_id}",
                         headers=auth(1, "ADMIN")).status_code == 200
    assert client.delete("/api/admin/catalog/badges/9",
                         headers=auth(1, "ADMIN")).status_code == 409

    created_product = client.post("/api/admin/catalog/products", headers=auth(1, "ADMIN"), json={
        "name": "测试文创", "category": "CULTURAL_CREATIVE", "cover_url": "/static/product.png",
        "origin_place": "天津", "story": "开发测试", "fund_rate_percent": 10,
        "status": "ON_SALE", "sku_name": "标准款", "price_cents": 12800, "stock": 10,
    })
    assert created_product.status_code == 200
    product = created_product.json()["data"]
    assert product["price_cents"] == 12800 and product["stock"] == 10
    updated_product = client.put(f"/api/admin/catalog/products/{product['id']}",
                                 headers=auth(1, "ADMIN"), json={
        "name": "测试文创", "category": "CULTURAL_CREATIVE", "cover_url": "/static/product.png",
        "origin_place": "天津", "story": "开发测试", "fund_rate_percent": 15,
        "status": "OFF_SALE", "sku_name": "标准款", "price_cents": 9900, "stock": 3,
    }).json()["data"]
    assert updated_product["status"] == "OFF_SALE" and updated_product["price_cents"] == 9900
    with client.sessions() as db:
        assert db.query(Product).count() == 1 and db.query(ProductSku).count() == 1

    created_exchange = client.post("/api/admin/catalog/exchange-items",
                                   headers=auth(1, "ADMIN"), json={
        "name": "兑换测试品", "energy_cost": 120, "stock": 5, "status": "ACTIVE",
    })
    assert created_exchange.status_code == 200
    item = created_exchange.json()["data"]
    updated_exchange = client.put(f"/api/admin/catalog/exchange-items/{item['id']}",
                                  headers=auth(1, "ADMIN"), json={
        "name": "兑换测试品", "energy_cost": 150, "stock": 0, "status": "INACTIVE",
    }).json()["data"]
    assert updated_exchange["energy_cost"] == 150 and updated_exchange["status"] == "INACTIVE"
    with client.sessions() as db:
        assert db.get(ExchangeItem, item["id"]).stock == 0
