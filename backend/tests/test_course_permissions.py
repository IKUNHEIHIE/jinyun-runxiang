"""Course management must be limited to administrators."""

import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import Course


class FakeSession:
    def __init__(self):
        self.course = Course(id=123, title="示例课程", status="PUBLISHED")
        self.commits = 0

    def add(self, course):
        course.id = 124
        self.course = course

    def commit(self):
        self.commits += 1

    def refresh(self, course):
        pass

    def query(self, model):
        assert model is Course
        return self

    def filter(self, *args):
        return self

    def first(self):
        return self.course


class CoursePermissionTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    @staticmethod
    def headers(role):
        token = create_access_token({"user_id": 1, "role_code": role})
        return {"Authorization": f"Bearer {token}"}

    def test_create_course_requires_admin(self):
        payload = {"title": "新课程"}
        self.assertEqual(self.client.post("/api/courses", json=payload).status_code, 401)
        self.assertEqual(
            self.client.post("/api/courses", json=payload, headers=self.headers("STUDENT")).status_code,
            403,
        )
        self.assertEqual(self.db.commits, 0)

        response = self.client.post("/api/courses", json=payload, headers=self.headers("ADMIN"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["id"], 124)
        self.assertEqual(self.db.commits, 1)

    def test_toggle_course_status_requires_admin(self):
        path = "/api/courses/123/status"
        self.assertEqual(self.client.put(path).status_code, 401)
        self.assertEqual(self.client.put(path, headers=self.headers("STUDENT")).status_code, 403)
        self.assertEqual(self.db.course.status, "PUBLISHED")
        self.assertEqual(self.db.commits, 0)

        response = self.client.put(path, headers=self.headers("ADMIN"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "OFFLINE")
        self.assertEqual(self.db.commits, 1)


if __name__ == "__main__":
    unittest.main()
