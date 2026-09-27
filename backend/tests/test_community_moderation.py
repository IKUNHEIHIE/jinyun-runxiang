"""A new community work must not be public before admin review."""

import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import CommunityPost, CommunityComment, CommunityLike, CommunityReport, ContentReview, SysUser


class Query:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.conditions = []

    def filter(self, *conditions):
        self.conditions.extend(conditions)
        return self

    def order_by(self, *args):
        return self

    def offset(self, value):
        return self

    def limit(self, value):
        return self

    def all(self):
        rows = self.db.rows[self.model]
        for expr in self.conditions:
            value = expr.right.value
            if expr.operator.__name__ == "in_op":
                rows = [row for row in rows if getattr(row, expr.left.name) in value]
            else:
                rows = [row for row in rows if getattr(row, expr.left.name) == value]
        return rows

    def first(self):
        return next(iter(self.all()), None)

    def count(self):
        return len(self.all())


class FakeSession:
    def __init__(self):
        self.rows = {
            CommunityPost: [],
            CommunityComment: [],
            CommunityLike: [],
            CommunityReport: [],
            ContentReview: [],
            SysUser: [
                SysUser(id=1, username="student", nickname="学生", role_code="STUDENT", status="ACTIVE"),
                SysUser(id=2, username="admin", nickname="管理员", role_code="ADMIN", status="ACTIVE"),
            ],
        }

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        if isinstance(row, (CommunityPost, CommunityComment, CommunityReport)):
            row.id = len(self.rows[type(row)]) + 1
            row.created_at = datetime.utcnow()
        if isinstance(row, CommunityPost):
            row.like_count = row.like_count or 0
            row.comment_count = row.comment_count or 0
            row.favorite_count = row.favorite_count or 0
            row.view_count = row.view_count or 0
        self.rows[type(row)].append(row)

    def commit(self):
        pass

    def refresh(self, row):
        pass


class CommunityModerationTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        self.student = self.headers(1, "STUDENT")
        self.admin = self.headers(2, "ADMIN")

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    @staticmethod
    def headers(user_id, role):
        token = create_access_token({"user_id": user_id, "role_code": role})
        return {"Authorization": f"Bearer {token}"}

    def test_post_is_hidden_until_admin_approves(self):
        create = self.client.post("/api/community/posts", json={
            "title": "皮影作品", "content": "我的作品", "cover_url": "/static/sample.png"
        }, headers=self.student)
        self.assertEqual(create.status_code, 200)
        self.assertEqual(create.json()["data"]["status"], "PENDING_REVIEW")
        self.assertEqual(self.client.get("/api/community/posts").json()["data"]["total"], 0)
        self.assertEqual(self.client.get("/api/community/posts/1").json()["code"], 4040)
        self.assertEqual(
            self.client.post("/api/community/posts/1/like", headers=self.student).json()["code"], 4090
        )
        self.assertEqual(self.client.post(
            "/api/admin/reviews/1/action", json={"action": "FEATURE"}, headers=self.admin
        ).json()["code"], 4090)
        self.assertEqual(self.client.post(
            "/api/admin/reviews/1/action", json={"action": "UNKNOWN"}, headers=self.admin
        ).status_code, 422)

        review = self.client.post("/api/admin/reviews/1/action", json={"action": "APPROVE"}, headers=self.admin)
        self.assertEqual(review.status_code, 200)
        self.assertEqual(self.client.get("/api/community/posts").json()["data"]["total"], 1)
        self.assertEqual(self.db.rows[ContentReview][0].reviewer_id, 2)

    def test_co_creation_requires_login(self):
        response = self.client.post("/api/community/posts/1/co-create", json={
            "co_creator_name": "同学", "colored_cover_url": "/static/sample.png", "co_note": "着色"
        })
        self.assertEqual(response.status_code, 401)

    def test_comments_and_reports_require_admin_review(self):
        self.client.post("/api/community/posts", json={
            "title": "皮影作品", "content": "我的作品", "cover_url": "/static/sample.png"
        }, headers=self.student)
        self.client.post("/api/admin/reviews/1/action", json={"action": "APPROVE"}, headers=self.admin)

        comment = self.client.post("/api/community/posts/1/comments", json={
            "content": "期待下一件作品"
        }, headers=self.student).json()["data"]
        self.assertEqual(comment["status"], "PENDING_REVIEW")
        detail = self.client.get("/api/community/posts/1").json()["data"]
        self.assertEqual(detail["comments"], [])
        self.assertEqual(detail["comment_count"], 0)
        self.assertEqual(self.client.get("/api/admin/comment-reviews", headers=self.student).status_code, 403)
        self.assertEqual(len(self.client.get("/api/admin/comment-reviews", headers=self.admin).json()["data"]), 1)
        approval = self.client.post(
            f"/api/admin/comment-reviews/{comment['id']}/action",
            json={"action": "APPROVE", "comment": "内容合规"}, headers=self.admin
        )
        self.assertEqual(approval.json()["data"]["status"], "APPROVED")
        self.assertEqual(len(self.client.get("/api/community/posts/1").json()["data"]["comments"]), 1)
        self.assertEqual(self.client.post(
            f"/api/admin/comment-reviews/{comment['id']}/action",
            json={"action": "APPROVE", "comment": "重复操作"}, headers=self.admin
        ).json()["code"], 4090)
        self.assertEqual(self.db.rows[CommunityPost][0].comment_count, 1)

        report = self.client.post("/api/community/reports", json={
            "post_id": 1, "reason": "盗用"
        }, headers=self.student).json()["data"]
        again = self.client.post("/api/community/reports", json={
            "post_id": 1, "reason": "盗用"
        }, headers=self.student).json()["data"]
        self.assertEqual(again["id"], report["id"])
        self.assertEqual(len(self.db.rows[CommunityReport]), 1)
        self.assertEqual(self.client.get("/api/admin/reports", headers=self.student).status_code, 403)
        action = self.client.post(f"/api/admin/reports/{report['id']}/action", json={
            "action": "OFFLINE_POST", "note": "核实盗用"
        }, headers=self.admin)
        self.assertEqual(action.json()["data"]["status"], "HANDLED")
        self.assertEqual(self.client.get("/api/community/posts/1").json()["code"], 4040)
        self.assertEqual(self.client.post(f"/api/admin/reports/{report['id']}/action", json={
            "action": "OFFLINE_POST", "note": "再次处理"
        }, headers=self.admin).json()["code"], 4090)


if __name__ == "__main__":
    unittest.main()
