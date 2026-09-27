"""Dashboard counts persisted business records instead of demo values."""

import unittest
from datetime import datetime

from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.admin import ResetPwdDTO, get_dashboard_data, reset_user_password
from app.core.database import Base
from app.core.security import verify_password
from app.models.entities import (
    Activity, ActivityAttendance, AiTask, AuthSession, CommunityComment, CommunityPost,
    CommunityReport, Course, LearningProgress, SysUser,
)


@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(type_, compiler, **kwargs):
    return "INTEGER"


class AdminDashboardTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine, tables=[model.__table__ for model in (
            Activity, ActivityAttendance, AiTask, AuthSession, CommunityComment, CommunityPost,
            CommunityReport, Course, LearningProgress, SysUser,
        )])
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_empty_dashboard_has_zero_counts_and_no_invented_activity(self):
        result = get_dashboard_data(current_user={"user_id": 1}, db=self.db)["data"]
        self.assertEqual(result["kpi"]["total_users"], 0)
        self.assertIsNone(result["kpi"]["dau"])
        self.assertEqual(result["pending_reviews"], {"posts": 0, "comments": 0, "reports": 0})
        self.assertEqual(len(result["trends"]), 7)
        self.assertTrue(all(day["course_completed"] == day["ai_tasks"] == 0 for day in result["trends"]))

    def test_counts_only_matching_records(self):
        now = datetime.utcnow()
        self.db.add_all([
            SysUser(id=1, username="admin", password_hash="x", nickname="管理员", role_code="ADMIN", status="ACTIVE"),
            Course(id=1, title="已发布课程", category="CRAFT", status="PUBLISHED", view_count=7),
            Course(id=2, title="草稿", category="CRAFT", status="DRAFT", view_count=100),
            LearningProgress(id=1, user_id=2, chapter_id=1, course_id=1, completed=True, completed_at=now),
            LearningProgress(id=2, user_id=2, chapter_id=2, course_id=1, completed=False),
            AiTask(task_id="task1", user_id=2, tool_type="TEXT", status="SUCCEEDED", input_json={}, created_at=now),
            CommunityPost(id=1, user_id=2, title="公开作品", status="APPROVED"),
            CommunityPost(id=2, user_id=2, title="待审作品", status="PENDING_REVIEW"),
            CommunityComment(id=1, post_id=1, user_id=2, content="待审", status="PENDING_REVIEW"),
            CommunityReport(id=1, post_id=1, reporter_id=2, reason="OTHER", status="PENDING"),
            Activity(id=1, title="体验", start_at=now, end_at=now, description="活动"),
            ActivityAttendance(id=1, activity_id=1, user_id=2),
        ])
        self.db.commit()
        result = get_dashboard_data(current_user={"user_id": 1}, db=self.db)["data"]
        self.assertEqual(result["kpi"]["total_posts"], 1)
        self.assertEqual(result["kpi"]["completed_chapters"], 1)
        self.assertEqual(result["kpi"]["ai_tasks"], 1)
        self.assertEqual(result["kpi"]["pending_reviews"], 3)
        self.assertEqual(result["kpi"]["attendances"], 1)
        self.assertEqual(result["hot_courses"][0]["title"], "已发布课程")
        self.assertEqual(result["trends"][-1]["course_completed"], 1)
        self.assertEqual(result["trends"][-1]["ai_tasks"], 1)

    def test_admin_password_reset_revokes_active_sessions(self):
        self.db.add_all([
            SysUser(id=3, username="learner", password_hash="old", nickname="学生", status="ACTIVE"),
            AuthSession(session_id="session-1", user_id=3, refresh_hash="abc",
                        expires_at=datetime(2099, 1, 1)),
        ])
        self.db.commit()
        reset_user_password(3, ResetPwdDTO(new_password="new-password"),
                            current_user={"user_id": 1}, db=self.db)
        self.assertTrue(verify_password("new-password", self.db.get(SysUser, 3).password_hash))
        self.assertIsNotNone(self.db.get(AuthSession, "session-1").revoked_at)


if __name__ == "__main__":
    unittest.main()
