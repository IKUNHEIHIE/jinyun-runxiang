"""Activity booking and on-site attendance keep capacity and rewards consistent."""

import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    Activity, ActivityReservation, ActivityAttendance, Badge, GrowthEvent,
    SysUser, UserBadge, UserGrowth,
)


class Query:
    def __init__(self, db, model):
        self.db, self.model, self.conditions = db, model, []

    def filter(self, *conditions):
        self.conditions.extend(conditions)
        return self

    def with_for_update(self):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        rows = self.db.rows[self.model]
        for expr in self.conditions:
            expected = expr.right.value
            if expr.operator.__name__ == "in_op":
                rows = [row for row in rows if getattr(row, expr.left.name) in expected]
            else:
                rows = [row for row in rows if getattr(row, expr.left.name) == expected]
        return rows

    def first(self):
        return next(iter(self.all()), None)

    def count(self):
        return len(self.all())


class FakeSession:
    def __init__(self):
        self.rows = {
            Activity: [], ActivityReservation: [], ActivityAttendance: [],
            Badge: [], GrowthEvent: [], UserBadge: [],
            UserGrowth: [UserGrowth(user_id=1, energy_value=0, level_code="LV1_APPRENTICE")],
            SysUser: [
                SysUser(id=1, username="student", nickname="学生", role_code="STUDENT", status="ACTIVE"),
                SysUser(id=2, username="admin", nickname="管理员", role_code="ADMIN", status="ACTIVE"),
                SysUser(id=3, username="other", nickname="其他学生", role_code="STUDENT", status="ACTIVE"),
            ],
        }

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        if hasattr(row, "id") and row.id is None:
            row.id = len(self.rows[type(row)]) + 1
        if isinstance(row, ActivityReservation):
            row.reserved_at = datetime.utcnow()
        if isinstance(row, ActivityAttendance):
            row.checked_at = datetime.utcnow()
        self.rows[type(row)].append(row)

    def commit(self):
        pass

    def refresh(self, row):
        pass


class ActivityAttendanceTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    @staticmethod
    def headers(user_id, role="STUDENT"):
        token = create_access_token({"user_id": user_id, "role_code": role})
        return {"Authorization": f"Bearer {token}"}

    def test_booking_capacity_and_attendance_code(self):
        admin = self.headers(2, "ADMIN")
        student = self.headers(1)
        other = self.headers(3)
        now = datetime.utcnow()
        payload = {
            "title": "皮影体验营", "type": "OFFLINE", "capacity": 1,
            "start_at": (now + timedelta(minutes=10)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "energy_reward": 25, "description": "现场体验", "status": "PUBLISHED",
        }
        self.assertEqual(self.client.post("/api/activities", json=payload, headers=student).status_code, 403)
        activity = self.client.post("/api/activities", json=payload, headers=admin).json()["data"]
        activity_id = activity["id"]
        self.assertEqual(self.client.put(
            f"/api/activities/{activity_id}/checkin-code", json={"code": "six-digits"}, headers=admin
        ).json()["code"], 0)
        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/reserve", headers=student
        ).json()["code"], 0)
        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/reserve", headers=student
        ).json()["code"], 0)
        self.assertEqual(self.db.rows[Activity][0].reserved_count, 1)
        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/reserve", headers=other
        ).json()["code"], 4090)

        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/cancel-reservation", headers=student
        ).json()["data"]["status"], "CANCELLED")
        self.assertEqual(self.db.rows[Activity][0].reserved_count, 0)
        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/reserve", headers=student
        ).json()["code"], 0)
        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/attend", json={"code": "wrong"}, headers=student
        ).json()["code"], 4030)
        attended = self.client.post(
            f"/api/activities/{activity_id}/attend", json={"code": "six-digits"}, headers=student
        ).json()["data"]
        self.assertEqual(attended["energy_added"], 25)
        self.assertEqual(self.client.post(
            f"/api/activities/{activity_id}/attend", json={"code": "six-digits"}, headers=student
        ).json()["data"]["energy_added"], 0)
        self.assertEqual(len(self.db.rows[ActivityAttendance]), 1)
        self.assertEqual(self.db.rows[UserGrowth][0].energy_value, 25)
        self.assertEqual(self.client.get(
            f"/api/activities/{activity_id}/stats", headers=admin
        ).json()["data"]["attended_count"], 1)
        self.assertEqual(self.client.post("/api/activities/checkin", json={
            "landmark_id": 7, "latitude": 39.0, "longitude": 117.0
        }, headers=student).json()["code"], 4100)


if __name__ == "__main__":
    unittest.main()
