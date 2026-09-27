"""Users may update only their own non-privileged profile fields."""

import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import SysUser, UserProfile


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
            SysUser: [
                SysUser(id=1, nickname="原昵称", role_code="STUDENT", status="ACTIVE"),
                SysUser(id=2, nickname="其他人", role_code="STUDENT", status="ACTIVE"),
            ],
            UserProfile: [],
        }
        self.commits = 0

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        self.rows[type(row)].append(row)

    def commit(self):
        self.commits += 1


class ProfileUpdateTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        token = create_access_token({"user_id": 1, "role_code": "STUDENT"})
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    def test_only_own_profile_fields_change(self):
        self.assertEqual(self.client.put("/api/auth/me", json={"nickname": "新昵称"}).status_code, 401)
        update = self.client.put("/api/auth/me", json={
            "nickname": "新昵称", "school_name": "乡村小学", "avatar_config": {"hair": "short"}
        }, headers=self.headers)
        self.assertEqual(update.status_code, 200)
        self.assertEqual(self.db.rows[SysUser][0].nickname, "新昵称")
        self.assertEqual(self.db.rows[SysUser][1].nickname, "其他人")
        self.assertEqual(self.db.rows[UserProfile][0].school_name, "乡村小学")
        self.assertEqual(self.db.commits, 1)

    def test_role_cannot_be_changed_via_profile(self):
        response = self.client.put("/api/auth/me", json={"role_code": "ADMIN"}, headers=self.headers)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.db.rows[SysUser][0].role_code, "STUDENT")
        self.assertEqual(self.db.commits, 0)


if __name__ == "__main__":
    unittest.main()
