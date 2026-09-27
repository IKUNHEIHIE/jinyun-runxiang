"""Without a device gateway, commands must not claim an ACK or execution."""

import unittest

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import Device, DeviceCommand, SysUser


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

    def all(self):
        return self.db.rows[self.model]


class FakeSession:
    def __init__(self):
        self.device = Device(
            id=7, device_code="robot-7", device_name="皮影设备",
            model="ROBOT_SHADOW_V1", firmware_version="1", status="ONLINE"
        )
        self.rows = {
            Device: [self.device], DeviceCommand: [],
            SysUser: [SysUser(id=1, username="teacher", nickname="教师", role_code="TEACHER", status="ACTIVE")],
        }

    def query(self, model):
        return Query(self, model)

    def add(self, row):
        self.rows[type(row)].append(row)

    def commit(self):
        pass


class DeviceCommandStateTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        token = create_access_token({"user_id": 1, "role_code": "TEACHER"})
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    def test_command_is_pending_until_real_ack(self):
        self.assertEqual(self.client.post("/api/devices/robot-7/command", json={
            "command_type": "RESET", "payload": {}
        }).status_code, 401)

        response = self.client.post("/api/devices/robot-7/command", json={
            "command_type": "RESET", "payload": {}
        }, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "PENDING")
        self.assertNotIn("executed_at", response.json()["data"])
        self.assertEqual(self.db.rows[DeviceCommand][0].status, "PENDING")
        self.assertIsNone(self.db.rows[DeviceCommand][0].sent_at)
        self.assertIsNone(self.db.rows[DeviceCommand][0].ack_at)
        self.assertIsNone(self.db.device.last_seen_at)

        listed = self.client.get("/api/devices").json()["data"][0]
        self.assertEqual(listed["telemetry"], {})


if __name__ == "__main__":
    unittest.main()
