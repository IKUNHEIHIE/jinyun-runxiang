"""Teachers cannot read or modify another teacher's class data."""

import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import Assignment, AssignmentSubmission, TeacherClass


class Query:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.conditions = []

    def filter(self, *conditions):
        self.conditions.extend(conditions)
        return self

    def first(self):
        return next((row for row in self.db.rows[self.model] if all(
            getattr(row, expr.left.name) == expr.right.value for expr in self.conditions
        )), None)


class FakeSession:
    def __init__(self):
        self.rows = {
            TeacherClass: [TeacherClass(id=123, teacher_id=2, name="别人的班", grade="小学三年级")],
            Assignment: [Assignment(id=55, class_id=123, teacher_id=2)],
            AssignmentSubmission: [AssignmentSubmission(id=77, assignment_id=55)],
        }
        self.writes = 0

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        self.writes += 1

    def commit(self):
        self.writes += 1


class TeacherBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        token = create_access_token({"user_id": 1, "role_code": "TEACHER"})
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    def test_cross_class_reads_and_writes_are_denied(self):
        cases = [
            self.client.get("/api/teacher/assignments?class_id=123", headers=self.headers),
            self.client.post("/api/teacher/assignments", json={
                "class_id": 123, "title": "作业", "description": "内容"
            }, headers=self.headers),
            self.client.get("/api/teacher/assignments/55/submissions", headers=self.headers),
            self.client.post("/api/teacher/submissions/77/review", json={
                "score": 90, "comment": "很好"
            }, headers=self.headers),
            self.client.get("/api/teacher/classes/123/analytics", headers=self.headers),
            self.client.get("/api/teacher/classes/123/exhibition-package", headers=self.headers),
        ]
        self.assertEqual([response.json()["code"] for response in cases], [4040] * len(cases))
        self.assertEqual(self.db.writes, 0)

    def test_exhibition_package_requires_login(self):
        response = self.client.get("/api/teacher/classes/123/exhibition-package")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
