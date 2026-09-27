"""New passwords use salted hashes and existing accounts migrate on login."""

import hashlib
import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.main import app
from app.models.entities import SysUser, AuthSession, UserGrowth


class Query:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.conditions = []

    def filter(self, *conditions):
        self.conditions.extend(conditions)
        return self

    def with_for_update(self):
        return self

    def first(self):
        return next((row for row in self.db.rows[self.model] if all(
            getattr(row, expr.left.name) == expr.right.value for expr in self.conditions
        )), None)


class FakeSession:
    def __init__(self):
        self.user = SysUser(
            id=1, username="student", nickname="学生", role_code="STUDENT",
            status="ACTIVE", password_hash=hashlib.sha256(b"sample-password").hexdigest()
        )
        self.rows = {SysUser: [self.user], AuthSession: [], UserGrowth: []}
        self.commits = 0

    def query(self, model):
        return Query(self, model)

    def commit(self):
        self.commits += 1

    def add(self, row):
        self.rows[type(row)].append(row)


class PasswordSecurityTests(unittest.TestCase):
    def test_salted_hash_and_legacy_verification(self):
        first = hash_password("sample-password")
        second = hash_password("sample-password")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("sample-password", first))
        self.assertFalse(verify_password("wrong", first))
        self.assertFalse(verify_password("sample-password", "scrypt$bad"))
        legacy = hashlib.sha256(b"sample-password").hexdigest()
        self.assertTrue(verify_password("sample-password", legacy))

    def test_login_upgrades_legacy_hash(self):
        db = FakeSession()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                response = client.post("/api/auth/login", json={
                    "username": "student", "password": "sample-password"
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["code"], 0)
                self.assertTrue(db.user.password_hash.startswith("scrypt$"))
                self.assertEqual(db.commits, 2)

                again = client.post("/api/auth/login", json={
                    "username": "student", "password": "sample-password"
                })
                self.assertEqual(again.json()["code"], 0)
                self.assertEqual(db.commits, 3)

                token = again.json()["data"]["token"]
                refresh_token = again.json()["data"]["refresh_token"]
                self.assertEqual(client.get("/api/auth/me", headers={
                    "Authorization": f"Bearer {refresh_token}"
                }).status_code, 401)
                rotated = client.post("/api/auth/refresh", json={
                    "refresh_token": refresh_token
                }).json()["data"]
                self.assertNotEqual(rotated["refresh_token"], refresh_token)
                self.assertEqual(client.post("/api/auth/refresh", json={
                    "refresh_token": refresh_token
                }).json()["code"], 4010)
                logout = client.post("/api/auth/logout", headers={
                    "Authorization": f"Bearer {token}"
                })
                self.assertEqual(logout.json()["code"], 0)
                self.assertEqual(client.get("/api/auth/me", headers={
                    "Authorization": f"Bearer {token}"
                }).status_code, 401)
                self.assertEqual(client.post("/api/auth/refresh", json={
                    "refresh_token": rotated["refresh_token"]
                }).json()["code"], 4010)
        finally:
            app.dependency_overrides.pop(get_db, None)


if __name__ == "__main__":
    unittest.main()
