"""AI tasks are private and model configuration is administrator-only."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import ai_workshop
from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import AiModel, AiTask


class Query:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.conditions = []

    def filter(self, *conditions):
        self.conditions.extend(conditions)
        return self

    def first(self):
        return next((row for row in self.all()), None)

    def all(self):
        return [row for row in self.db.rows[self.model] if all(
            getattr(row, expr.left.name) == expr.right.value for expr in self.conditions
        )]


class FakeSession:
    def __init__(self):
        self.task = AiTask(
            task_id="task-one", user_id=1, tool_type="SHADOW_PUPPET",
            status="QUEUED", progress=10, model_version="1.0.0", input_json={}
        )
        self.model = AiModel(
            id=7, code="demo", name="原模型", task_type="IMAGE", version="1",
            provider="local", config_json={}, prompt_template="", status="ACTIVE", is_default=True
        )
        self.rows = {AiTask: [self.task], AiModel: [self.model]}
        self.commits = 0
        self.closed = False

    def query(self, model):
        return Query(self, model)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


class AiPermissionTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        self.owner = self.headers(1, "STUDENT")
        self.other = self.headers(2, "STUDENT")
        self.admin = self.headers(3, "ADMIN")

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)

    @staticmethod
    def headers(user_id, role):
        token = create_access_token({"user_id": user_id, "role_code": role})
        return {"Authorization": f"Bearer {token}"}

    def test_only_owner_or_admin_can_read_or_cancel_task(self):
        path = "/api/ai/tasks/task-one"
        self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get(path, headers=self.other).json()["code"], 4040)
        self.assertEqual(self.client.post(path + "/cancel", headers=self.other).json()["code"], 4040)
        self.assertEqual(self.db.commits, 0)
        self.assertEqual(self.client.get(path, headers=self.owner).json()["data"]["task_id"], "task-one")
        self.assertEqual(self.client.post(path + "/cancel", headers=self.owner).json()["data"]["status"], "CANCELLED")
        self.assertEqual(self.db.commits, 1)

    def test_model_management_requires_admin(self):
        path = "/api/ai/models/7"
        self.assertEqual(self.client.put(path, json={"name": "新模型"}).status_code, 401)
        self.assertEqual(self.client.put(path, json={"name": "新模型"}, headers=self.owner).status_code, 403)
        self.assertEqual(self.client.get("/api/ai/models?all_status=true").json()["code"], 4030)
        self.assertEqual(self.db.model.name, "原模型")
        self.assertEqual(self.client.put(path, json={"name": "新模型"}, headers=self.admin).status_code, 200)
        self.assertEqual(self.db.model.name, "新模型")

    def test_cancelled_task_does_not_run(self):
        self.db.task.status = "CANCELLED"
        with patch.object(ai_workshop, "SessionLocal", return_value=self.db):
            ai_workshop.execute_ai_inference("task-one", "SHADOW_PUPPET", 1)
        self.assertEqual(self.db.task.status, "CANCELLED")
        self.assertEqual(self.db.commits, 0)
        self.assertTrue(self.db.closed)


if __name__ == "__main__":
    unittest.main()
