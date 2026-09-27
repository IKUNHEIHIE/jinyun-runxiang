"""Exercise course chapter lookup and idempotent learning progress reports."""

import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    Course, CourseChapter, GrowthEvent, LearningProgress, OfflineSyncEvent,
    Quiz, QuizQuestion, QuizAttempt, SysUser, UserGrowth,
)


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
            Quiz: [],
            QuizQuestion: [],
            QuizAttempt: [],
            LearningProgress: [],
            OfflineSyncEvent: [],
            GrowthEvent: [],
            UserGrowth: [UserGrowth(user_id=1, energy_value=0, level_code="LV1_APPRENTICE")],
            SysUser: [
                SysUser(id=1, username="student", nickname="学生", role_code="STUDENT", status="ACTIVE"),
                SysUser(id=2, username="admin", nickname="管理员", role_code="ADMIN", status="ACTIVE"),
            ],
        }
        self.commits = 0

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        if hasattr(row, "id") and row.id is None:
            row.id = 1000 + len(self.rows[type(row)])
        self.rows[type(row)].append(row)

    def commit(self):
        self.commits += 1

    def refresh(self, row):
        pass

    def delete(self, row):
        self.rows[type(row)].remove(row)


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

    def test_offline_sync_merges_valid_events_and_reports_conflicts(self):
        progress = {"course_id": 123, "chapter_id": 456, "position_seconds": 50,
                    "duration_seconds": 60, "completed": True}
        def event(event_id, payload, event_time="2026-09-22T12:00:00Z"):
            return {"event_id": event_id, "event_type": "PROGRESS_UPDATE",
                    "payload": payload, "event_time": event_time}

        batch = [
            event("good", progress),
            event("later", {**progress, "position_seconds": 10, "completed": False}),
            event("wrong-chapter", {**progress, "chapter_id": 999}),
            event("bad-date", progress, "not-a-date"),
            event("negative", {**progress, "position_seconds": -1}),
            {**event("unsupported", progress), "event_type": "QUIZ_SUBMIT"},
            event("contradictory", progress),
            event("contradictory", {**progress, "position_seconds": 2}),
        ]
        response = self.client.post("/api/courses/sync-offline", json={"events": batch}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["success_event_ids"], ["good", "later"])
        self.assertEqual(response.json()["data"]["conflict_event_ids"],
                         ["wrong-chapter", "bad-date", "negative", "unsupported", "contradictory"])
        self.assertEqual(len(self.db.rows[OfflineSyncEvent]), 2)
        self.assertEqual(len(self.db.rows[LearningProgress]), 1)
        self.assertEqual(self.db.rows[LearningProgress][0].position_seconds, 50)
        self.assertTrue(self.db.rows[LearningProgress][0].completed)
        self.assertEqual(self.db.rows[UserGrowth][0].energy_value, 10)
        self.assertEqual(len(self.db.rows[GrowthEvent]), 1)

        retry = self.client.post("/api/courses/sync-offline", json={"events": [batch[0], batch[0]]}, headers=self.headers)
        self.assertEqual(retry.json()["data"]["success_event_ids"], ["good"])
        self.assertEqual(len(self.db.rows[GrowthEvent]), 1)

        admin_token = create_access_token({"user_id": 2, "role_code": "ADMIN"})
        other_headers = {"Authorization": f"Bearer {admin_token}"}
        stolen = self.client.post("/api/courses/sync-offline", json={"events": [batch[0]]}, headers=other_headers)
        self.assertEqual(stolen.json()["data"]["conflict_event_ids"], ["good"])

    def test_admin_can_manage_chapters_and_quiz_without_leaking_answers(self):
        admin_token = create_access_token({"user_id": 2, "role_code": "ADMIN"})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        chapter_path = "/api/courses/123/chapters"
        payload = {"seq": 2, "title": "第二章", "duration_seconds": 120}
        self.assertEqual(self.client.post(chapter_path, json=payload, headers=self.headers).status_code, 403)
        chapter = self.client.post(chapter_path, json=payload, headers=admin_headers).json()["data"]
        self.assertEqual(chapter["course_id"], 123)
        self.assertEqual(self.client.put(
            f"{chapter_path}/{chapter['id']}", json={"title": "新标题"}, headers=admin_headers
        ).json()["code"], 0)

        quiz = self.client.post("/api/courses/123/quizzes", json={
            "title": "小测", "chapter_id": chapter["id"], "pass_score": 10
        }, headers=admin_headers).json()["data"]
        question_url = f"/api/courses/quiz/{quiz['id']}/questions"
        question_data = {
            "seq": 1, "type": "SINGLE", "content": "正确的是？",
            "options": [{"key": "A", "text": "正确"}, {"key": "B", "text": "错误"}],
            "answers": ["A"], "score": 10,
        }
        self.assertEqual(self.client.post(question_url, json=question_data, headers=self.headers).status_code, 403)
        question = self.client.post(question_url, json=question_data, headers=admin_headers).json()["data"]
        public_quiz = self.client.get(f"/api/courses/quiz/{quiz['id']}").json()["data"]
        self.assertNotIn("answers", public_quiz["questions"][0])
        self.assertNotIn("answer_json", public_quiz["questions"][0])
        self.assertEqual(self.client.post(question_url, json={
            **question_data, "seq": 2, "answers": ["Z"]
        }, headers=admin_headers).json()["code"], 4000)

        attempt = self.client.post(f"/api/courses/quiz/{quiz['id']}/submit", json={
            "answers": {str(question["id"]): ["A"]}
        }, headers=self.headers).json()["data"]
        self.assertTrue(attempt["passed"])
        self.assertEqual(attempt["energy_reward"], 20)
        self.assertEqual(self.client.delete(
            f"{question_url}/{question['id']}", headers=admin_headers
        ).json()["code"], 4090)

        self.db.rows[Course][0].status = "OFFLINE"
        self.assertEqual(self.client.get(f"/api/courses/quiz/{quiz['id']}").json()["code"], 4040)
        self.assertEqual(self.client.post(f"/api/courses/quiz/{quiz['id']}/submit", json={
            "answers": {str(question["id"]): ["A"]}
        }, headers=self.headers).json()["code"], 4040)


if __name__ == "__main__":
    unittest.main()
