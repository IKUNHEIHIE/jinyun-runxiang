"""Persistent resources required by the MasterGo mobile flows."""
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, JSON, Date, DateTime, Integer, Numeric, UniqueConstraint
from app.core.database import Base


class HeritageEntry(Base):
    __tablename__ = "heritage_entry"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    era = Column(String(128))
    summary = Column(String(1000))
    cover_url = Column(String(500))
    model_url = Column(String(500))
    content_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(16), nullable=False, default="PUBLISHED")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCollection(Base):
    __tablename__ = "user_collection"
    user_id = Column(BigInteger, primary_key=True)
    target_type = Column(String(16), primary_key=True)
    target_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserFollow(Base):
    __tablename__ = "user_follow"
    follower_id = Column(BigInteger, primary_key=True)
    followed_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CourseRating(Base):
    __tablename__ = "course_rating"
    user_id = Column(BigInteger, primary_key=True)
    course_id = Column(BigInteger, primary_key=True)
    score = Column(Integer, nullable=False)
    comment = Column(String(1000), nullable=False, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    content = Column(Text, nullable=False)
    contact = Column(String(128))
    status = Column(String(16), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    reply_text = Column(Text, default="")
    handled_by = Column(BigInteger)
    handled_at = Column(DateTime)


class LearningDay(Base):
    __tablename__ = "learning_day"
    user_id = Column(BigInteger, primary_key=True)
    day = Column(Date, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LessonPlanRecord(Base):
    __tablename__ = "lesson_plan_record"
    __table_args__ = (UniqueConstraint("teacher_id", "request_id", name="uk_lesson_plan_request"),)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    teacher_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    grade = Column(String(64), nullable=False)
    topic = Column(String(128), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    content_json = Column(JSON, nullable=False)
    source = Column(String(128), nullable=False)
    request_id = Column(String(64))
    request_mode = Column(String(16))
    created_at = Column(DateTime, default=datetime.utcnow)


class ClassNotice(Base):
    __tablename__ = "class_notice"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    class_id = Column(BigInteger, nullable=False, index=True)
    teacher_id = Column(BigInteger, nullable=False)
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClassAttendance(Base):
    __tablename__ = "class_attendance"
    class_id = Column(BigInteger, primary_key=True)
    student_id = Column(BigInteger, primary_key=True)
    day = Column(String(10), primary_key=True)
    status = Column(String(16), nullable=False)
    recorded_by = Column(BigInteger, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClassSession(Base):
    __tablename__ = "class_session"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    class_id = Column(BigInteger, nullable=False, index=True)
    host_id = Column(BigInteger, nullable=False)
    title = Column(String(128), nullable=False)
    stream_url = Column(String(500))
    status = Column(String(16), nullable=False, default="LIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)


class ClassMessage(Base):
    __tablename__ = "class_message"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    type = Column(String(16), nullable=False, default="CHAT")
    content = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExchangeItem(Base):
    __tablename__ = "exchange_item"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    cover_url = Column(String(500))
    energy_cost = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    status = Column(String(16), nullable=False, default="ACTIVE")


class EnergyExchange(Base):
    __tablename__ = "energy_exchange"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(String(64), nullable=False, unique=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    item_id = Column(BigInteger, nullable=False)
    item_name = Column(String(128), nullable=False)
    energy_cost = Column(Integer, nullable=False)
    receiver_name = Column(String(64), nullable=False)
    receiver_phone = Column(String(32), nullable=False)
    receiver_address = Column(String(255), nullable=False)
    status = Column(String(16), nullable=False, default="REQUESTED")
    tracking_no = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
    handling_note = Column(String(500), nullable=False, default="")
    handled_by = Column(BigInteger)
    handled_at = Column(DateTime)


class WalkSession(Base):
    __tablename__ = "walk_session"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    active_seconds = Column(Integer, nullable=False, default=0)
    distance_meters = Column(Integer, nullable=False, default=0)
    status = Column(String(16), nullable=False, default="ACTIVE")
    last_latitude = Column(Numeric(10, 6))
    last_longitude = Column(Numeric(10, 6))
    last_point_at = Column(DateTime)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)


class CommunityPostDetail(Base):
    __tablename__ = "community_post_detail"
    post_id = Column(BigInteger, primary_key=True)
    gallery_json = Column(JSON, nullable=False, default=list)
    specifications_json = Column(JSON, nullable=False, default=list)
    appreciation_json = Column(JSON, nullable=False, default=list)


class CommunityCommentLike(Base):
    __tablename__ = "community_comment_like"
    comment_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
