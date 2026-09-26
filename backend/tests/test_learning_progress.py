"""Exercise course chapter lookup and idempotent learning progress reports."""

import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import Course, CourseChapter, GrowthEvent, LearningProgress, UserGrowth


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

    def matches(self, row):
        return all(getattr(row, expr.left.name) == expr.right.value for expr in self.conditions)

    def first(self):
        return next((row for row in self.db.rows[self.model] if self.matches(row)), None)

    def all(self):
        return [row for row in self.db.rows[self.model] if self.matches(row)]


class FakeSession:
    def __init__(self):
        self.rows = {
            Course: [Course(id=123, title="示例课程", status="PUBLISHED")],
            CourseChapter: [CourseChapter(id=456, course_id=123, seq=1, title="第一章", duration_seconds=60)],
            LearningProgress: [],
            GrowthEvent: [],
            UserGrowth: [UserGrowth(user_id=1, energy_value=0, level_code="LV1_APPRENTICE")],
        }
        self.commits = 0

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        self.rows[type(row)].append(row)

    def commit(self):
        self.commits += 1


class LearningProgressTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        token = create_access_token({"user_id": 1, "role_code": "STUDENT"})
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    def test_chapters_and_progress_query(self):
        chapters = self.client.get("/api/courses/123/chapters")
        self.assertEqual(chapters.status_code, 200)
        self.assertEqual(chapters.json()["data"][0]["id"], 456)
        self.assertEqual(self.client.get("/api/learning/progress").status_code, 401)
        progress = self.client.get("/api/learning/progress", headers=self.headers)
        self.assertEqual(progress.status_code, 200)
        self.assertEqual(progress.json()["data"], [])

    def test_unpublished_chapters_and_catalog_are_hidden(self):
        self.db.rows[Course][0].status = "OFFLINE"
        chapters = self.client.get("/api/courses/123/chapters")
        self.assertEqual(chapters.json()["code"], 4040)
        detail = self.client.get("/api/courses/123")
        self.assertEqual(detail.json()["code"], 4040)
        catalog = self.client.get("/api/courses?status=ALL")
        self.assertEqual(catalog.json()["code"], 4030)

        admin_token = create_access_token({"user_id": 2, "role_code": "ADMIN"})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        chapters = self.client.get("/api/courses/123/chapters", headers=admin_headers)
        self.assertEqual(chapters.json()["data"][0]["id"], 456)

    def test_reports_merge_without_duplicate_rewards(self):
        payload = {
            "course_id": 123, "chapter_id": 456,
            "position_seconds": 50, "duration_seconds": 60, "completed": True,
        }
        first = self.client.post("/api/learning/progress", json=payload, headers=self.headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["data"]["energy_added"], 10)

        payload["position_seconds"] = 10
        payload["completed"] = False
        second = self.client.post("/api/courses/progress", json=payload, headers=self.headers)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["data"]["energy_added"], 0)
        self.assertTrue(second.json()["data"]["completed"])

        progress = self.client.get("/api/learning/progress?course_id=123", headers=self.headers)
        self.assertEqual(progress.json()["data"][0]["position_seconds"], 50)
        self.assertEqual(self.db.rows[UserGrowth][0].energy_value, 10)
        self.assertEqual(len(self.db.rows[GrowthEvent]), 1)

    def test_invalid_chapter_and_negative_position_do_not_write(self):
        payload = {
            "course_id": 123, "chapter_id": 999,
            "position_seconds": 50, "duration_seconds": 60, "completed": True,
        }
        response = self.client.post("/api/learning/progress", json=payload, headers=self.headers)
        self.assertEqual(response.json()["code"], 4040)
        self.assertEqual(self.db.commits, 0)

        payload["chapter_id"] = 456
        payload["position_seconds"] = -1
        response = self.client.post("/api/learning/progress", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.db.commits, 0)

        payload["position_seconds"] = 10
        self.db.rows[Course][0].status = "OFFLINE"
        response = self.client.post("/api/learning/progress", json=payload, headers=self.headers)
        self.assertEqual(response.json()["code"], 4040)
        self.assertEqual(self.db.commits, 0)


if __name__ == "__main__":
    unittest.main()
