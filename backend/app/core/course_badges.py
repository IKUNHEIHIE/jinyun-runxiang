"""Course completion rules for the badges shown in the supplied design.

The design supplies names/artwork, not thresholds. The implemented rule is one
published course with all of its chapters completed. Awards remain historical
when a teacher subsequently changes a course; they never grant extra energy.
"""
from collections import defaultdict

from app.models.entities import Badge, Course, CourseChapter, LearningProgress, UserBadge


COURSE_BADGES = (
    ("BADGE_COURSE_SHADOW_PUPPET", "SHADOW_PUPPET", "皮影匠人", "bc52c81d0e175da3a49348211b675cf1.png"),
    ("BADGE_COURSE_BRONZE", "BRONZE", "青铜识者", "4cc6cb3f6ab3a8d4cbdf86b44932bf1f.png"),
    ("BADGE_COURSE_PAPER_CUTTING", "PAPER_CUTTING", "剪纸巧手", "c60d4e28eba132cbad29c60d05c5c637.png"),
    ("BADGE_COURSE_EMBROIDERY", "EMBROIDERY", "苏绣传人", "4cc84984603424f83df22a2b5254cad5.png"),
    ("BADGE_COURSE_CERAMICS", "CERAMICS", "瓷韵匠心", "99c4fb71f5018df0bf9aeaa227050cdd.png"),
)
COURSE_BADGE_CATEGORIES = {code: category for code, category, _, _ in COURSE_BADGES}


def course_badge_progress(db, user_id):
    """Count whole courses, never completed chapters from different courses."""
    rows = db.query(Course.id, Course.category, CourseChapter.id).join(
        CourseChapter, CourseChapter.course_id == Course.id).filter(
        Course.status == "PUBLISHED", Course.category.in_(COURSE_BADGE_CATEGORIES.values())
    ).order_by(Course.id, CourseChapter.seq, CourseChapter.id).all()
    completed = set(db.query(LearningProgress.course_id, LearningProgress.chapter_id).filter(
        LearningProgress.user_id == user_id, LearningProgress.completed.is_(True)).all()) if user_id else set()
    courses = {}
    for course_id, category, chapter_id in rows:
        course = courses.setdefault(course_id, {"category": category, "completed": True})
        course["completed"] &= (course_id, chapter_id) in completed
    result = defaultdict(lambda: {"completed_courses": 0, "available_courses": 0, "recommended_course_id": None})
    for course_id, course in courses.items():
        progress = result[course["category"]]
        progress["available_courses"] += 1
        progress["completed_courses"] += int(course["completed"])
        if progress["recommended_course_id"] is None or not course["completed"]:
            progress["recommended_course_id"] = course_id
    return result


def award_course_badges(db, user_id):
    """Caller holds the user row lock; flush and award in its transaction."""
    db.flush()
    progress = course_badge_progress(db, user_id)
    owned = {row.badge_id for row in db.query(UserBadge).filter_by(user_id=user_id).all()}
    awarded = []
    for badge in db.query(Badge).filter(Badge.code.in_(COURSE_BADGE_CATEGORIES)).all():
        if badge.id not in owned and progress[COURSE_BADGE_CATEGORIES[badge.code]]["completed_courses"] >= 1:
            db.add(UserBadge(user_id=user_id, badge_id=badge.id))
            owned.add(badge.id)
            awarded.append(badge.code)
    return awarded
