"""Offline regression coverage for the 2026-10-16 audit; never uses a live DB."""
import hashlib
import json
import os
import re
import secrets
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock
from types import SimpleNamespace
from loguru import logger

os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(48))
os.environ["DATABASE_URL"] = "sqlite://"

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core import files, asset_generator
from app.core.config import Settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.api import ai_workshop, heritage
from app.models.entities import (
    SysUser, UserGrowth, Course, AiModel, Product, ProductSku, Badge, UserBadge,
    CommunityPost, TeacherClass, Assignment, AssignmentSubmission, AiTask,
    OrderMain, OrderItem, FundRecord, Asset, GrowthEvent, CourseChapter, OfflineSyncEvent,
)

logger.disable("app")


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class SecurityRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password_hash = hash_password("test-password-123")

    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)

        def isolated_db():
            with self.sessions() as db:
                yield db

        app.dependency_overrides[get_db] = isolated_db
        self.directory = tempfile.TemporaryDirectory()
        self.static = Path(self.directory.name)
        (self.static / "uploads").mkdir()
        (self.static / "generated").mkdir()
        self.patches = [
            patch.object(files, "STATIC_DIR", self.static),
            patch.object(ai_workshop, "STATIC_UPLOADS_DIR", str(self.static / "uploads")),
            patch.object(heritage, "STATIC_GENERATED_DIR", str(self.static / "generated")),
            patch.object(asset_generator, "STATIC_GENERATED_DIR", str(self.static / "generated")),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(app)
        with self.sessions() as db:
            db.add_all([
                SysUser(id=i, username=f"user-{i}", nickname=f"user-{i}", password_hash=self.password_hash,
                        role_code=role, status="ACTIVE", token_version=0)
                for i, role in [(1, "ADMIN"), (2, "TEACHER"), (3, "STUDENT"), (4, "TEACHER")]
            ])
            db.add_all([
                UserGrowth(user_id=3, energy_value=100),
                Course(id=1, title="test-course", category="SHADOW_PUPPET", status="PUBLISHED"),
                CourseChapter(id=1, course_id=1, title="chapter", duration_seconds=60),
                AiModel(id=1, code="test-model", name="test-model", task_type="SHADOW_PUPPET"),
                Product(id=1, name="first", cover_url="/x.png", fund_rate_percent=10),
                Product(id=2, name="second", cover_url="/x.png", fund_rate_percent=90),
                ProductSku(id=1, product_id=1, sku_code="first", name="first", price_cents=100, stock=10),
                Badge(id=1, code="SEAL_TEST", name="seal", description="test", icon_url="/x.svg"),
                UserBadge(user_id=3, badge_id=1),
                CommunityPost(id=1, user_id=3, title="pending", content="private", status="PENDING_REVIEW"),
                CommunityPost(id=2, user_id=3, title="public", content="public", status="APPROVED"),
                TeacherClass(id=1, teacher_id=2, name="owned-class", grade="grade"),
                Assignment(id=1, class_id=1, teacher_id=2, title="homework", description="test",
                           deadline=datetime.utcnow() + timedelta(days=1)),
                AssignmentSubmission(id=1, assignment_id=1, student_id=3, content="private-homework"),
                AiTask(task_id="test-task", user_id=3, tool_type="SHADOW_PUPPET", input_json={"prompt": "private"}),
            ])
            db.commit()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        for item in reversed(self.patches):
            item.stop()
        self.engine.dispose()
        self.directory.cleanup()

    def auth(self, uid=3, role="STUDENT", version=0):
        return {"Authorization": "Bearer " + create_access_token(
            {"sub": str(uid), "user_id": uid, "role_code": role, "token_version": version})}

    def order(self, quantity=1, product=1):
        return self.client.post("/api/mall/orders", headers=self.auth(), json={
            "items": [{"product_id": product, "sku_id": 1, "quantity": quantity}],
            "receiver_name": "test", "receiver_phone": "123456", "receiver_address": "test-address"})

    def test_management_requires_admin(self):
        self.assertEqual(self.client.put("/api/courses/1/status").status_code, 401)
        self.assertEqual(self.client.put("/api/ai/models/1", json={"status": "DISABLED"}).status_code, 401)
        self.assertEqual(self.client.post("/api/courses", headers=self.auth(), json={"title": "test"}).status_code, 403)
        self.assertEqual(self.client.put("/api/courses/1/status", headers=self.auth(1, "ADMIN")).status_code, 200)

    def test_nonexistent_and_wrong_role_tokens_fail(self):
        self.assertEqual(self.client.get("/api/admin/users", headers=self.auth(999, "ADMIN")).status_code, 401)
        self.assertEqual(self.client.get("/api/admin/users", headers=self.auth(3, "ADMIN")).status_code, 401)
        forged = jwt.encode({"sub": "1", "user_id": 1, "role_code": "ADMIN",
                             "iat": datetime.utcnow(), "exp": datetime.utcnow() + timedelta(minutes=5),
                             "token_version": 0}, "jinyun_runxiang_super_secret_key_2026_tianjin_heritage", algorithm="HS256")
        self.assertEqual(self.client.get("/api/admin/users", headers={"Authorization": "Bearer " + forged}).status_code, 401)

    def test_disable_and_reenable_revoke_old_token(self):
        headers = self.auth()
        for state in ["DISABLED", "ACTIVE"]:
            self.assertEqual(self.client.put("/api/admin/users/3/status", headers=self.auth(1, "ADMIN"), json={"status": state}).status_code, 200)
            self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)

    def test_password_reset_and_logout_revoke_tokens(self):
        old = self.auth()
        self.assertEqual(self.client.post("/api/admin/users/3/reset-password", headers=self.auth(1, "ADMIN"), json={"new_password": "another-password"}).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me", headers=old).status_code, 401)
        login = self.client.post("/api/auth/login", json={"username": "user-3", "password": "another-password"}).json()
        self.assertEqual(login["code"], 0)
        headers = {"Authorization": "Bearer " + login["data"]["token"]}
        self.assertEqual(self.client.post("/api/auth/logout", headers=headers).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me", headers=headers).status_code, 401)

    def test_password_upgrade_and_registration(self):
        legacy = hashlib.sha256(b"test-password-123").hexdigest()
        with self.sessions() as db:
            db.get(SysUser, 3).password_hash = legacy
            db.commit()
        result = self.client.post("/api/auth/login", json={"username": "user-3", "password": "test-password-123"})
        self.assertEqual(result.json()["code"], 0)
        with self.sessions() as db:
            self.assertTrue(db.get(SysUser, 3).password_hash.startswith("pbkdf2_sha256$"))
        registered = self.client.post("/api/auth/register", json={"username": "new-user", "password": "new-password", "nickname": "test", "role_code": "ADMIN"}).json()
        self.assertEqual(registered["data"]["user"]["role_code"], "STUDENT")
        self.assertTrue(verify_password("test-password-123", self.password_hash))
        self.assertNotEqual(hash_password("same-password"), hash_password("same-password"))

    def test_teacher_ownership(self):
        other = self.auth(4, "TEACHER")
        self.assertEqual(self.client.get("/api/teacher/assignments/1/submissions", headers=other).status_code, 404)
        self.assertEqual(self.client.post("/api/teacher/submissions/1/review", headers=other, json={"score": 0, "comment": "test"}).status_code, 404)
        self.assertEqual(self.client.get("/api/teacher/classes/1/analytics", headers=other).status_code, 404)
        owner = self.auth(2, "TEACHER")
        self.assertEqual(self.client.get("/api/teacher/assignments/1/submissions", headers=owner).status_code, 200)
        self.assertEqual(self.client.post("/api/teacher/submissions/1/review", headers=owner, json={"score": 90, "comment": "good"}).status_code, 200)

    def test_task_owner_and_anonymous_access(self):
        self.assertEqual(self.client.get("/api/ai/tasks/test-task").status_code, 401)
        self.assertEqual(self.client.post("/api/ai/tasks/test-task/cancel").status_code, 401)
        result = self.client.get("/api/ai/tasks/test-task", headers=self.auth(4, "TEACHER")).json()
        self.assertNotEqual(result["code"], 0)
        self.assertEqual(self.client.get("/api/ai/tasks/test-task", headers=self.auth()).json()["code"], 0)
        self.assertEqual(self.client.post("/api/ai/tasks/test-task/cancel", headers=self.auth()).json()["code"], 0)

    def test_pending_post_and_co_creation(self):
        self.assertEqual(self.client.get("/api/community/posts/1").status_code, 404)
        self.assertEqual(self.client.get("/api/community/posts/1", headers=self.auth()).status_code, 200)
        payload = {"co_creator_name": "test", "colored_cover_url": "/x.svg", "co_note": "test"}
        self.assertEqual(self.client.post("/api/community/posts/2/co-create", json=payload).status_code, 401)
        response = self.client.post("/api/community/posts/2/co-create", headers=self.auth(), json=payload).json()
        with self.sessions() as db:
            post = db.get(CommunityPost, response["data"]["co_post_id"])
            self.assertEqual(post.user_id, 3)
            self.assertEqual(post.status, "PENDING_REVIEW")
            self.assertFalse(post.is_featured)

    def test_invalid_order_quantities_and_sku(self):
        for quantity in [-2, 0, 101]:
            self.assertEqual(self.order(quantity).status_code, 422)
        self.assertEqual(self.order(product=2).status_code, 404)
        with self.sessions() as db:
            self.assertEqual(db.get(ProductSku, 1).stock, 10)
            self.assertEqual(db.query(OrderMain).count(), 0)

    def test_order_snapshots_pending_certificate_and_cancel(self):
        result = self.order(2).json()["data"]
        self.assertEqual(result["status"], "CREATED")
        with self.sessions() as db:
            self.assertEqual(db.get(ProductSku, 1).stock, 8)
            self.assertEqual(db.query(OrderItem).one().quantity, 2)
            self.assertEqual(db.query(FundRecord).count(), 0)
            self.assertIsNone(db.query(OrderMain).one().pay_time)
        order_no = result["order_no"]
        self.assertEqual(self.client.get(f"/api/mall/orders/{order_no}/certificate", headers=self.auth()).status_code, 409)
        for _ in range(2):
            self.assertEqual(self.client.post(f"/api/mall/orders/{order_no}/cancel", headers=self.auth()).status_code, 200)
        with self.sessions() as db:
            self.assertEqual(db.get(ProductSku, 1).stock, 10)

    def test_file_traversal_and_ownership(self):
        for url in ["/static/../secret.txt", "/static/%2e%2e/secret.txt", "C:/secret.txt", "https://other.invalid/a.svg"]:
            result = self.client.post("/api/heritage/seals/stamp", headers=self.auth(), json={"seal_code": "SEAL_TEST", "svg_url": url})
            self.assertIn(result.status_code, [400, 404])
        self.assertEqual(self.client.post("/api/heritage/seals/stamp", json={"seal_code": "SEAL_TEST", "svg_raw": "x"}).status_code, 401)

    def test_svg_active_content_rejected_and_valid_upload_stamps(self):
        malicious = [
            '<svg xmlns="http://www.w3.org/2000/svg" onload = "alert(1)"/>',
            '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
            '<svg xmlns="http://www.w3.org/2000/svg"><use href="javascript:alert(1)"/></svg>',
            '<!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><svg xmlns="http://www.w3.org/2000/svg">&xxe;</svg>',
        ]
        for content in malicious:
            response = self.client.post("/api/ai/assets/upload", headers=self.auth(), files={"file": ("test.svg", content, "image/svg+xml")})
            self.assertEqual(response.status_code, 400)
        valid = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1000"><rect width="10" height="10"/></svg>'
        response = self.client.post("/api/ai/assets/upload", headers=self.auth(), files={"file": ("test.svg", valid, "image/svg+xml")})
        url = response.json()["data"]["file_url"]
        stamped = self.client.post("/api/heritage/seals/stamp", headers=self.auth(), json={"seal_code": "SEAL_TEST", "svg_url": url})
        self.assertEqual(stamped.json()["code"], 0)

    def test_html_export_escapes_and_requires_teacher(self):
        payload = {"topic": '<svg onload="alert(1)"></svg>'}
        self.assertEqual(self.client.get("/api/teacher/lesson-plans/export-html", params=payload).status_code, 401)
        result = self.client.get("/api/teacher/lesson-plans/export-html", params=payload, headers=self.auth(2, "TEACHER"))
        self.assertEqual(result.status_code, 200)
        self.assertNotIn('<svg onload=', result.text)
        self.assertIn('&lt;svg', result.text)

    def test_svg_generators_preserve_safe_text(self):
        content = asset_generator.generate_shadow_puppet_svg('</text><script>alert(1)</script><text>')
        self.assertNotIn('<script>', content)
        for function, args in [
            (asset_generator.generate_shadow_puppet_svg, []),
            (asset_generator.generate_shadow_puppet_template_svg, []),
            (asset_generator.generate_bronze_taotie_svg, []),
            (asset_generator.generate_ballad_sheet_svg, []),
            (asset_generator.generate_lacquer_raden_svg, []),
            (asset_generator.generate_mesh_preview_svg, []),
        ]:
            files.sanitize_svg(function(*args))

    def test_invalid_artwork_never_rewards(self):
        for _ in range(2):
            self.assertEqual(self.client.post("/api/ai/evaluate", headers=self.auth(), json={"image_url": "/does-not-exist.png"}).status_code, 404)
        with self.sessions() as db:
            self.assertEqual(db.get(UserGrowth, 3).energy_value, 100)
            self.assertEqual(db.query(GrowthEvent).count(), 0)

    def test_vision_receives_image_and_reward_is_idempotent(self):
        path = self.static / "uploads" / "work.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n-test-image")
        with self.sessions() as db:
            db.add(Asset(asset_type="IMAGE", object_key="uploads/work.png", file_url="/static/uploads/work.png",
                         mime_type="image/png", created_by=3))
            db.commit()
        client = MagicMock()
        evaluation = {"total_score": 90, "stars": 4, "composition_score": 90,
                      "color_score": 90, "technique_score": 90,
                      "composition_feedback": "composition", "color_feedback": "color",
                      "technique_feedback": "technique", "mentor_comment": "feedback"}
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(evaluation)))])
        with patch.object(ai_workshop, "get_llm_client_and_config", return_value=(client, {"vision_model_name": "test-vision"})):
            for expected_reward in [30, 0]:
                result = self.client.post("/api/ai/evaluate", headers=self.auth(), json={"image_url": "/static/uploads/work.png"})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["data"]["energy_reward"], expected_reward)
        message = client.chat.completions.create.call_args.kwargs["messages"][0]["content"][1]
        self.assertTrue(message["image_url"]["url"].startswith("data:image/png;base64,"))
        with self.sessions() as db:
            self.assertEqual(db.get(UserGrowth, 3).energy_value, 130)
            self.assertEqual(db.query(GrowthEvent).count(), 1)

    def test_unconfigured_vision_never_fabricates_score(self):
        path = self.static / "uploads" / "work.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n-test-image")
        with self.sessions() as db:
            db.add(Asset(asset_type="IMAGE", object_key="uploads/work.png", file_url="/static/uploads/work.png",
                         mime_type="image/png", created_by=3))
            db.commit()
        result = self.client.post("/api/ai/evaluate", headers=self.auth(), json={"image_url": "/static/uploads/work.png"})
        self.assertEqual(result.status_code, 503)
        with self.sessions() as db:
            self.assertEqual(db.get(UserGrowth, 3).energy_value, 100)

    def test_offline_sync_partial_ack_and_retry(self):
        valid = {"event_id": "valid-1", "event_type": "PROGRESS_UPDATE", "event_time": "2026-10-16T10:00:00Z",
                 "payload": {"course_id": 1, "chapter_id": 1, "position_seconds": 60, "duration_seconds": 60, "completed": True}}
        invalid = {**valid, "event_id": "invalid-1", "payload": {**valid["payload"], "chapter_id": 999}}
        for _ in range(2):
            result = self.client.post("/api/courses/sync-offline", headers=self.auth(), json={"events": [invalid, valid]}).json()["data"]
            self.assertEqual(result["success_event_ids"], ["valid-1"])
            self.assertEqual(result["conflict_event_ids"], ["invalid-1"])
        with self.sessions() as db:
            self.assertEqual(db.query(OfflineSyncEvent).count(), 1)
            self.assertEqual(db.get(UserGrowth, 3).energy_value, 110)
        result = self.client.post("/api/courses/sync-offline", headers=self.auth(4, "TEACHER"), json={"events": [valid]}).json()["data"]
        self.assertEqual(result["success_event_ids"], [])
        self.assertEqual(result["conflict_event_ids"], ["valid-1"])

    def test_cancelled_worker_never_completes_or_rewards(self):
        with self.sessions() as db:
            db.get(AiTask, "test-task").status = "CANCELLED"
            db.commit()
        with patch.object(ai_workshop, "SessionLocal", self.sessions):
            ai_workshop.execute_ai_inference("test-task", "SHADOW_PUPPET", 3)
        with self.sessions() as db:
            self.assertEqual(db.get(AiTask, "test-task").status, "CANCELLED")
            self.assertEqual(db.query(GrowthEvent).count(), 0)

    def test_cancel_during_generation_is_not_overwritten(self):
        generate = ai_workshop.generate_shadow_puppet_svg

        def cancel_then_generate(*args, **kwargs):
            with self.sessions() as db:
                db.get(AiTask, "test-task").status = "CANCELLED"
                db.commit()
            return generate(*args, **kwargs)

        with patch.object(ai_workshop, "SessionLocal", self.sessions), patch.object(
            ai_workshop, "generate_shadow_puppet_svg", side_effect=cancel_then_generate
        ):
            ai_workshop.execute_ai_inference("test-task", "SHADOW_PUPPET", 3)
        with self.sessions() as db:
            self.assertEqual(db.get(AiTask, "test-task").status, "CANCELLED")
            self.assertEqual(db.query(GrowthEvent).count(), 0)
            self.assertEqual(db.query(Asset).count(), 0)

    def test_full_schema_contains_every_mapped_column(self):
        sql = (Path(__file__).resolve().parents[2] / "database/schema_all.sql").read_text(encoding="utf-8")
        tables = {name: body for name, body in re.findall(
            r"CREATE TABLE IF NOT EXISTS `?(\w+)`?\s*\((.*?)\n\)", sql, re.S)}
        for table in Base.metadata.tables.values():
            self.assertIn(table.name, tables)
            columns = set(re.findall(r"^\s*`?(\w+)`?\s+(?:BIGINT|INT|INTEGER|VARCHAR|CHAR|TEXT|DATETIME|DATE|BOOLEAN|TINYINT|JSON|NUMERIC|DECIMAL)",
                                     tables[table.name], re.M | re.I))
            self.assertTrue(set(table.columns.keys()) <= columns, (table.name, set(table.columns.keys()) - columns))

    def test_default_secret_rejected(self):
        for value in ["short", "jinyun_runxiang_super_secret_key_2026_tianjin_heritage"]:
            with self.assertRaises(ValueError):
                Settings(_env_file=None, JWT_SECRET_KEY=value)

    def test_demo_seed_passwords_match(self):
        seed = (Path(__file__).resolve().parents[2] / "database/seed_data.sql").read_text(encoding="utf-8")
        for username, password in [("admin", "admin123"), ("teacher_wang", "teacher123"), ("student_ming", "student123")]:
            stored = re.search(r"\(\d+, '" + username + r"', '([^']+)'", seed).group(1)
            self.assertTrue(verify_password(password, stored))

    def test_health_and_honest_metrics(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        overview = self.client.get("/api/screen/overview").json()["data"]
        self.assertEqual(overview["donation_orders"], [])
        self.assertEqual(overview["kpis"][1]["value"], "1")
        self.assertEqual(overview["kpis"][3]["value"], "0.00")


if __name__ == "__main__":
    unittest.main()
