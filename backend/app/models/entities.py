import json
from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, DateTime,
    Boolean, JSON, Numeric, ForeignKey
)
from app.core.database import Base

# 1. 身份与用户域
class SysUser(Base):
    __tablename__ = "sys_user"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(64), nullable=False)
    avatar_url = Column(String(500))
    role_code = Column(String(32), default="STUDENT", nullable=False)
    grade = Column(String(32))
    status = Column(String(16), default="ACTIVE", nullable=False)
    phone = Column(String(32))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profile"
    user_id = Column(BigInteger, primary_key=True)
    school_name = Column(String(128))
    district = Column(String(64))
    bio = Column(String(255))
    avatar_config_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserGrowth(Base):
    __tablename__ = "user_growth"
    user_id = Column(BigInteger, primary_key=True)
    energy_value = Column(Integer, default=0, nullable=False)
    level_code = Column(String(32), default="LV1_APPRENTICE", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GrowthEvent(Base):
    __tablename__ = "growth_event"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    event_type = Column(String(32), nullable=False)
    ref_id = Column(String(64), nullable=False)
    value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Badge(Base):
    __tablename__ = "badge"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(64), nullable=False)
    description = Column(String(255), nullable=False)
    icon_url = Column(String(500), nullable=False)
    condition_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserBadge(Base):
    __tablename__ = "user_badge"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    badge_id = Column(BigInteger, nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

# 2. 教学与学习域
class Course(Base):
    __tablename__ = "course"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    subtitle = Column(String(255))
    category = Column(String(32), nullable=False)
    age_group = Column(String(32), default="PRIMARY_LOW", nullable=False)
    cover_url = Column(String(500))
    cover_asset_id = Column(BigInteger)
    description = Column(Text)
    duration_minutes = Column(Integer, default=0)
    energy_reward = Column(Integer, default=50)
    view_count = Column(Integer, default=0)
    status = Column(String(16), default="PUBLISHED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CourseChapter(Base):
    __tablename__ = "course_chapter"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, nullable=False)
    seq = Column(Integer, default=1)
    title = Column(String(128), nullable=False)
    video_url = Column(String(500))
    duration_seconds = Column(Integer, default=0)
    key_points_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    chapter_id = Column(BigInteger, nullable=False)
    course_id = Column(BigInteger, nullable=False)
    position_seconds = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    last_learned_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OfflineSyncEvent(Base):
    __tablename__ = "offline_sync_event"
    event_id = Column(String(64), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    event_type = Column(String(32), nullable=False)
    payload_json = Column(JSON, nullable=False)
    event_time = Column(DateTime, nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow)

class Quiz(Base):
    __tablename__ = "quiz"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    course_id = Column(BigInteger, nullable=False)
    chapter_id = Column(BigInteger)
    title = Column(String(128), nullable=False)
    pass_score = Column(Integer, default=60)
    energy_reward = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizQuestion(Base):
    __tablename__ = "quiz_question"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quiz_id = Column(BigInteger, nullable=False)
    seq = Column(Integer, default=1)
    type = Column(String(16), default="SINGLE")
    content = Column(Text, nullable=False)
    options_json = Column(JSON, nullable=False)
    answer_json = Column(JSON, nullable=False)
    explanation = Column(Text)
    score = Column(Integer, default=10)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempt"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quiz_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    score = Column(Integer, default=0)
    passed = Column(Boolean, default=False)
    answer_json = Column(JSON, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

# 3. AI工坊与媒资域
class Asset(Base):
    __tablename__ = "asset"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(32), nullable=False)
    object_key = Column(String(500), nullable=False)
    bucket = Column(String(64), default="jinyun-assets")
    file_url = Column(String(500))
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(BigInteger, default=0)
    sha256 = Column(String(64))
    metadata_json = Column(JSON)
    visibility = Column(String(16), default="PUBLIC")
    created_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)

class AiModel(Base):
    __tablename__ = "ai_model"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(64), nullable=False)
    name = Column(String(128), nullable=False)
    task_type = Column(String(32), nullable=False)
    version = Column(String(32), default="1.0.0")
    provider = Column(String(64), default="LOCAL_WORKER")
    config_json = Column(JSON)
    prompt_template = Column(Text)
    status = Column(String(16), default="ACTIVE")
    is_default = Column(Boolean, default=False)

class AiTask(Base):
    __tablename__ = "ai_task"
    task_id = Column(String(32), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    tool_type = Column(String(32), nullable=False)
    status = Column(String(20), default="QUEUED")
    progress = Column(Integer, default=0)
    model_id = Column(BigInteger)
    model_version = Column(String(64))
    input_json = Column(JSON, nullable=False)
    result_summary_json = Column(JSON)
    error_code = Column(String(32))
    error_message = Column(String(500))
    trace_id = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 4. 社区与内容风控
class CommunityTopic(Base):
    __tablename__ = "community_topic"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(String(500))
    cover_url = Column(String(500))
    post_count = Column(Integer, default=0)
    status = Column(String(16), default="ACTIVE")

class CommunityPost(Base):
    __tablename__ = "community_post"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    title = Column(String(128), nullable=False)
    content = Column(Text)
    category = Column(String(32), default="SHADOW_PUPPET")
    cover_url = Column(String(500))
    source_task_id = Column(String(32))
    topic_id = Column(BigInteger)
    status = Column(String(20), default="PENDING_REVIEW")
    is_featured = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    heritage_master_like = Column(Boolean, default=False)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CommunityComment(Base):
    __tablename__ = "community_comment"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    reply_to_id = Column(BigInteger)
    content = Column(String(1000), nullable=False)
    status = Column(String(16), default="APPROVED")
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityLike(Base):
    __tablename__ = "community_like"
    post_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CommunityReport(Base):
    __tablename__ = "community_report"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, nullable=False)
    reporter_id = Column(BigInteger, nullable=False)
    reason = Column(String(64), nullable=False)
    description = Column(String(500))
    status = Column(String(16), default="PENDING")
    handled_by = Column(BigInteger)
    handled_note = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    handled_at = Column(DateTime)

class ContentReview(Base):
    __tablename__ = "content_review"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    target_type = Column(String(32), default="COMMUNITY_POST")
    target_id = Column(BigInteger, nullable=False)
    risk_level = Column(String(16), default="LOW")
    result = Column(String(20), default="PENDING")
    ai_analysis_json = Column(JSON)
    reviewer_id = Column(BigInteger)
    review_comment = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)

# 5. 教师域
class TeacherClass(Base):
    __tablename__ = "teacher_class"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    teacher_id = Column(BigInteger, nullable=False)
    name = Column(String(64), nullable=False)
    grade = Column(String(32), nullable=False)
    school_id = Column(String(64))
    invite_code = Column(String(16))
    student_count = Column(Integer, default=0)
    status = Column(String(16), default="ACTIVE")

class ClassMember(Base):
    __tablename__ = "class_member"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    class_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    status = Column(String(16), default="ACTIVE")
    joined_at = Column(DateTime, default=datetime.utcnow)

class Assignment(Base):
    __tablename__ = "assignment"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    class_id = Column(BigInteger, nullable=False)
    teacher_id = Column(BigInteger, nullable=False)
    course_id = Column(BigInteger)
    title = Column(String(128), nullable=False)
    type = Column(String(32), default="AI_CREATION")
    tool_type = Column(String(32))
    deadline = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    rubric_json = Column(JSON)
    status = Column(String(16), default="PUBLISHED")
    created_at = Column(DateTime, default=datetime.utcnow)

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submission"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    assignment_id = Column(BigInteger, nullable=False)
    student_id = Column(BigInteger, nullable=False)
    content = Column(Text)
    asset_id = Column(BigInteger)
    source_task_id = Column(String(32))
    status = Column(String(20), default="SUBMITTED")
    submitted_at = Column(DateTime, default=datetime.utcnow)

class AssignmentReview(Base):
    __tablename__ = "assignment_review"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    submission_id = Column(BigInteger, nullable=False, unique=True)
    teacher_id = Column(BigInteger)
    score = Column(Integer, default=90)
    comment = Column(Text)
    ai_suggestion_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# 6. 活动与文旅地标
class HeritageLandmark(Base):
    __tablename__ = "heritage_landmark"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    address = Column(String(255), nullable=False)
    district = Column(String(64), nullable=False)
    latitude = Column(Numeric(10, 6), nullable=False)
    longitude = Column(Numeric(10, 6), nullable=False)
    geofence_radius_meters = Column(Integer, default=500)
    description = Column(Text)
    cover_url = Column(String(500))
    status = Column(String(16), default="ACTIVE")

class Activity(Base):
    __tablename__ = "activity"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    type = Column(String(32), default="OFFLINE")
    landmark_id = Column(BigInteger)
    master_name = Column(String(64))
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)
    capacity = Column(Integer, default=100)
    reserved_count = Column(Integer, default=0)
    energy_reward = Column(Integer, default=30)
    status = Column(String(16), default="PUBLISHED")
    description = Column(Text, nullable=False)

class ActivityReservation(Base):
    __tablename__ = "activity_reservation"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    status = Column(String(16), default="CONFIRMED")
    reserved_at = Column(DateTime, default=datetime.utcnow)

class ActivityCheckin(Base):
    __tablename__ = "activity_checkin"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_id = Column(BigInteger)
    landmark_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    latitude = Column(Numeric(10, 6), nullable=False)
    longitude = Column(Numeric(10, 6), nullable=False)
    distance_meters = Column(Integer, nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)

# 7. 电商助农与基金
class Product(Base):
    __tablename__ = "product"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    category = Column(String(32), default="CULTURAL_CREATIVE")
    cover_url = Column(String(500), nullable=False)
    origin_place = Column(String(128))
    story = Column(Text)
    fund_rate_percent = Column(Numeric(5, 2), default=10.00)
    status = Column(String(16), default="ON_SALE")

class ProductSku(Base):
    __tablename__ = "product_sku"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, nullable=False)
    sku_code = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    price_cents = Column(Integer, default=0)
    stock = Column(Integer, default=100)

class OrderMain(Base):
    __tablename__ = "order_main"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), unique=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    total_amount_cents = Column(Integer, default=0)
    fund_amount_cents = Column(Integer, default=0)
    status = Column(String(24), default="CREATED")
    receiver_name = Column(String(64))
    receiver_phone = Column(String(32))
    receiver_address = Column(String(255))
    pay_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class FundRecord(Base):
    __tablename__ = "fund_record"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_order_id = Column(BigInteger, nullable=False)
    amount_cents = Column(Integer, default=0)
    purpose = Column(String(128), default="乡村小学非遗美育耗材捐赠")
    status = Column(String(16), default="ALLOCATED")
    created_at = Column(DateTime, default=datetime.utcnow)

# 8. 具身智能设备
class Device(Base):
    __tablename__ = "device"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_code = Column(String(64), unique=True, nullable=False)
    device_name = Column(String(128), nullable=False)
    model = Column(String(64), default="ROBOT_SHADOW_V1")
    firmware_version = Column(String(32), default="1.0.0")
    school_id = Column(String(64))
    status = Column(String(16), default="OFFLINE")
    last_seen_at = Column(DateTime)

class DeviceCommand(Base):
    __tablename__ = "device_command"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    command_id = Column(String(64), unique=True, nullable=False)
    device_id = Column(BigInteger, nullable=False)
    command_type = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=False)
    status = Column(String(16), default="SENT")
    sent_at = Column(DateTime, default=datetime.utcnow)
    ack_at = Column(DateTime)

# 9. 运营管控与统计
class BannerConfig(Base):
    __tablename__ = "banner_config"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    image_url = Column(String(500), nullable=False)
    link_url = Column(String(500))
    position = Column(String(32), default="HOME_TOP")
    sort_no = Column(Integer, default=1)
    status = Column(String(16), default="ACTIVE")

class OperationStatDaily(Base):
    __tablename__ = "operation_stat_daily"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stat_date = Column(DateTime, unique=True, nullable=False)
    dau = Column(Integer, default=0)
    mau = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    course_learn_count = Column(Integer, default=0)
    ai_generate_count = Column(Integer, default=0)
    community_post_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    order_gmv_cents = Column(Integer, default=0)
    fund_added_cents = Column(Integer, default=0)
    device_active_count = Column(Integer, default=0)
