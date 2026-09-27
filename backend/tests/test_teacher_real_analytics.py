"""Teacher dashboard rates come from class records, not fixed example numbers."""

import unittest
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.entities import (
    Assignment, AssignmentReview, AssignmentSubmission, ClassMember, Course, LearningProgress,
    QuizAttempt, SysUser, TeacherClass, UserGrowth, UserProfile,
)


@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(type_, compiler, **kwargs):
    return "INTEGER"


class TeacherAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        tables = [model.__table__ for model in (
            Assignment, AssignmentReview, AssignmentSubmission, ClassMember, Course, LearningProgress,
            QuizAttempt, SysUser, TeacherClass, UserGrowth, UserProfile,
        )]
        Base.metadata.create_all(self.engine, tables=tables)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            SysUser(id=1, username="teacher", password_hash="x", nickname="教师", role_code="TEACHER", status="ACTIVE"),
            SysUser(id=2, username="student", password_hash="x", nickname="学生", role_code="STUDENT", status="ACTIVE"),
            SysUser(id=3, username="outsider", password_hash="x", nickname="外班学生", role_code="STUDENT", status="ACTIVE"),
            TeacherClass(id=10, teacher_id=1, name="非遗一班", grade="三年级", status="ACTIVE", student_count=1),
            ClassMember(id=20, class_id=10, student_id=2, status="ACTIVE"),
            Course(id=30, title="皮影", category="SHADOW_PUPPET", status="PUBLISHED"),
            LearningProgress(id=40, user_id=2, course_id=30, chapter_id=50, position_seconds=60,
                             duration_seconds=60, completed=True, last_learned_at=datetime.utcnow()),
            LearningProgress(id=41, user_id=2, course_id=30, chapter_id=51, position_seconds=10,
                             duration_seconds=60, completed=False, last_learned_at=datetime.utcnow()),
            QuizAttempt(id=60, quiz_id=70, user_id=2, score=80, passed=True, answer_json={}),
            QuizAttempt(id=61, quiz_id=70, user_id=2, score=40, passed=False, answer_json={}),
            Assignment(id=80, class_id=10, teacher_id=1, title="作业一", type="AI_CREATION",
                       deadline=datetime.utcnow() + timedelta(days=1), description="做皮影", status="PUBLISHED"),
            Assignment(id=81, class_id=10, teacher_id=1, title="作业二", type="AI_CREATION",
                       deadline=datetime.utcnow() + timedelta(days=1), description="画皮影", status="PUBLISHED"),
            AssignmentSubmission(id=90, assignment_id=80, student_id=2, content="作品", status="SUBMITTED"),
            UserGrowth(user_id=2, energy_value=30, level_code="LV1_APPRENTICE"),
        ])
        self.db.commit()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        token = create_access_token({"user_id": 1, "role_code": "TEACHER"})
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.pop(get_db, None)
        self.db.close()
        self.engine.dispose()

    def test_rates_change_with_persisted_class_data(self):
        response = self.client.get("/api/teacher/classes/10/analytics", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["course_completion_rate"], 50.0)
        self.assertEqual(data["quiz_pass_rate"], 50.0)
        self.assertEqual(data["homework_submit_rate"], 50.0)
        self.assertEqual(data["category_preference"], [{"name": "SHADOW_PUPPET", "count": 2}])
        self.assertEqual(data["radar_capabilities"], [])

    def test_only_class_members_can_submit(self):
        student_token = create_access_token({"user_id": 2, "role_code": "STUDENT"})
        outsider_token = create_access_token({"user_id": 3, "role_code": "STUDENT"})
        student = {"Authorization": f"Bearer {student_token}"}
        outsider = {"Authorization": f"Bearer {outsider_token}"}
        path = "/api/teacher/assignments/81/submit"
        self.assertEqual(self.client.post(path, json={"content": "新作品"}, headers=outsider).json()["code"], 4030)
        submitted = self.client.post(path, json={"content": "新作品"}, headers=student)
        self.assertEqual(submitted.status_code, 200)
        submission_id = submitted.json()["data"]["id"]
        self.assertEqual(self.client.get("/api/teacher/classes/10/analytics", headers=self.headers)
                         .json()["data"]["homework_submit_rate"], 100.0)
        submissions = self.client.get("/api/teacher/assignments/81/submissions", headers=self.headers).json()["data"]
        self.assertEqual(submissions[0]["id"], submission_id)
        reviewed = self.client.post(f"/api/teacher/submissions/{submission_id}/review", json={
            "score": 92, "comment": "完成得很好"
        }, headers=self.headers)
        self.assertEqual(reviewed.json()["code"], 0)
        exhibition = self.client.get("/api/teacher/classes/10/exhibition-package", headers=self.headers).json()["data"]
        self.assertEqual(exhibition["exhibit_count"], 1)
        self.assertEqual(exhibition["items"][0]["student_name"], "学生")
        self.assertEqual(exhibition["items"][0]["mentor_critique"], "完成得很好")
        self.assertIsNone(exhibition["items"][0]["colored_image_url"])
        self.assertEqual(self.client.post(path, json={"content": "修改版"}, headers=student).json()["code"], 4090)


if __name__ == "__main__":
    unittest.main()
