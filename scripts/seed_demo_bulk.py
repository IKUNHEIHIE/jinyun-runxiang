"""Generate 200 demo courses and 200 demo community posts.

Run inside the backend environment (DATABASE_URL points at the target database):
    python scripts/seed_demo_bulk.py            # dry run
    python scripts/seed_demo_bulk.py --apply    # write
    python scripts/seed_demo_bulk.py --rollback # remove what this marker created


Dry-run by default; --apply writes.  Idempotent through a SysConfig marker: a second
run refuses to add another batch unless --force is passed.
"""
import argparse
import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.core.database import SessionLocal
from app.models.entities import (CommunityComment, CommunityPost, Course, CourseChapter,
                                 SysConfig, SysUser)
from app.models.mobile import CommunityPostDetail

DESIGN_DIR = Path(os.environ.get("DEMO_DESIGN_DIR") or (REPO / "backend" / "static" / "design"))
MARKER = "demo_bulk_seed_20261021"
TARGET_COURSES = 200
TARGET_POSTS = 200
VIDEOS = [
    "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
    "https://media.w3.org/2010/05/sintel/trailer.mp4",
]

CRAFTS = [
    ("皮影", "SHADOW_PUPPET"), ("剪纸", "PAPER_CUTTING"), ("彩塑", "CLAY_FIGURINE"),
    ("年画", "NEW_YEAR_PAINTING"), ("瓷器", "CERAMICS"), ("刺绣", "EMBROIDERY"),
    ("风筝", "KITE"), ("青铜", "BRONZE"),
]
TOPICS = ["起稿", "刀工", "配色", "纹样", "光影", "构图", "材质", "技法", "临摹", "鉴赏"]
VARIANTS = [("入门", "PRIMARY_LOW"), ("精讲", "PRIMARY_HIGH"), ("工坊", "PRIMARY_HIGH")]
POST_OBJECTS = {
    "SHADOW_PUPPET": "旦角影人", "PAPER_CUTTING": "团花窗花", "CLAY_FIGURINE": "仕女彩塑",
    "NEW_YEAR_PAINTING": "门神年画", "CERAMICS": "青花梅瓶", "EMBROIDERY": "折枝海棠",
    "KITE": "沙燕风筝", "BRONZE": "饕餮纹鼎",
}
POST_ACTIONS = ["观察记录", "创作手记", "临摹练习", "工坊成品", "课堂作业"]
POST_DETAILS = ["线条", "配色", "构图", "光影", "细节"]
COMMENTS = [
    "刀口的转折很干净，想请教一下起稿的顺序。",
    "配色很稳，红与金的比重拿捏得好。",
    "光影层次出来了，边缘再收一点会更利落。",
    "这个纹样我在课堂上临过，老师的讲法很受用。",
    "构图留白舒服，适合做成文创小件。",
    "材质的表现很真实，釉色的过渡很自然。",
    "线条有呼吸感，学习了。",
    "配色偏暖，和年画的调子很搭。",
    "细节处理得很耐心，佩服。",
    "整体完成度很高，可以作为范例。",
    "想问一下工具，是刻刀还是剪子？",
    "第二张的光影更好，层次更清楚。",
]


def covers():
    names = sorted(p.name for p in DESIGN_DIR.glob("*.png"))
    return [f"/static/design/{name}" for name in names] or ["/static/design/demo-cover.png"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()

    rng = random.Random(20261021)
    now = datetime.utcnow()
    cover_pool = covers()

    with SessionLocal() as db:
        marker = db.query(SysConfig).filter_by(config_key=MARKER).first()
        if args.rollback:
            if not marker:
                print(json.dumps({"rolled_back": False, "reason": "no marker"}))
                return
            payload = json.loads(marker.config_value)
            course_ids, post_ids = payload.get("course_ids", []), payload.get("post_ids", [])
            deleted = {
                "chapters": db.query(CourseChapter).filter(CourseChapter.course_id.in_(course_ids)).delete(synchronize_session=False),
                "courses": db.query(Course).filter(Course.id.in_(course_ids)).delete(synchronize_session=False),
                "comments": db.query(CommunityComment).filter(CommunityComment.post_id.in_(post_ids)).delete(synchronize_session=False),
                "details": db.query(CommunityPostDetail).filter(CommunityPostDetail.post_id.in_(post_ids)).delete(synchronize_session=False),
                "posts": db.query(CommunityPost).filter(CommunityPost.id.in_(post_ids)).delete(synchronize_session=False),
            }
            db.delete(marker)
            db.commit()
            print(json.dumps({"rolled_back": True, **deleted, "courses_left": db.query(Course).count(),
                              "posts_left": db.query(CommunityPost).count()}, ensure_ascii=False))
            return
        if marker and not args.force:
            print(json.dumps({"skipped": True, "marker": json.loads(marker.config_value)}, ensure_ascii=False))
            return

        students = [u.id for u in db.query(SysUser).filter(SysUser.role_code == "STUDENT").all()]
        if not students:
            raise SystemExit("no student accounts")

        combos = [(craft, code, topic, variant, age)
                  for craft, code in CRAFTS for topic in TOPICS for variant, age in VARIANTS]
        rng.shuffle(combos)

        courses = []
        chapters = []
        for index in range(TARGET_COURSES):
            craft, code, topic, variant, age = combos[index % len(combos)]
            title = f"{craft}·{topic}{variant}"
            if index >= len(combos):
                title = f"{title}（第{index // len(combos) + 1}期）"
            created = now - timedelta(days=rng.randint(1, 120), hours=rng.randint(0, 23))
            course = Course(
                title=title,
                subtitle=f"{variant}课程 · {'1-3年级' if age == 'PRIMARY_LOW' else '4-6年级'}",
                category=code,
                age_group=age,
                cover_url=cover_pool[index % len(cover_pool)],
                description=(f"围绕{craft}的{topic}展开，从观察实物到完成一件小作品，"
                             f"每节课留有动手练习与讲评时间。"),
                duration_minutes=rng.choice([30, 40, 45, 60, 75, 90]),
                energy_reward=rng.choice([30, 40, 50, 60, 80]),
                view_count=rng.randint(20, 900),
                status="PUBLISHED",
                created_at=created,
                updated_at=created,
            )
            courses.append(course)

        if args.apply:
            for course in courses:
                db.add(course)
            db.flush()
            for course in courses:
                for seq, (chapter_title, points) in enumerate([
                    (f"认识{craft}", ["观察实物", "记录特征", "说出感受"]),
                    (f"{topic}要领", ["工具与手势", "分解动作", "常见问题"]),
                    ("示范与练习", ["跟随示范", "独立完成", "互评"]),
                    ("作品讲评", ["对照范例", "修改细节", "归档"]),
                ], start=1):
                    chapters.append(CourseChapter(
                        course_id=course.id, seq=seq, title=chapter_title,
                        video_url=VIDEOS[(course.id + seq) % len(VIDEOS)],
                        duration_seconds=rng.randint(300, 720),
                        key_points_json=points, created_at=course.created_at,
                    ))
            db.add_all(chapters)
            db.flush()

        posts = []
        details = []
        comments = []
        if args.apply:
            for index in range(TARGET_POSTS):
                craft, code = CRAFTS[index % len(CRAFTS)]
                action = POST_ACTIONS[index % len(POST_ACTIONS)]
                detail = POST_DETAILS[index % len(POST_DETAILS)]
                cover = cover_pool[index % len(cover_pool)]
                created = now - timedelta(days=rng.randint(0, 60), hours=rng.randint(0, 23))
                likes = rng.randint(0, 80)
                post = CommunityPost(
                    user_id=rng.choice(students),
                    title=f"{POST_OBJECTS[code]} · {action}（{detail}）",
                    content=(f"这次围绕{POST_OBJECTS[code]}做了一次{action}，"
                             f"重点放在{detail}上，完成后对照课堂笔记做了修改。"),
                    category=code,
                    cover_url=cover,
                    status="APPROVED",
                    like_count=likes,
                    comment_count=0,
                    favorite_count=rng.randint(0, 20),
                    view_count=rng.randint(20, 600),
                    created_at=created,
                )
                posts.append(post)
            db.add_all(posts)
            db.flush()
            for post in posts:
                gallery = [post.cover_url]
                if rng.random() < 0.3:
                    gallery.append(cover_pool[(cover_pool.index(post.cover_url) + 7) % len(cover_pool)])
                details.append(CommunityPostDetail(post_id=post.id, gallery_json=gallery,
                                                  specifications_json=[], appreciation_json=[]))
                for _ in range(rng.randint(1, 2)):
                    comments.append(CommunityComment(
                        post_id=post.id, user_id=rng.choice(students), content=rng.choice(COMMENTS),
                        status="APPROVED", like_count=rng.randint(0, 6),
                        created_at=post.created_at + timedelta(hours=rng.randint(1, 48)),
                    ))
            db.add_all(details)
            db.add_all(comments)
            db.flush()
            for post in posts:
                post.comment_count = sum(1 for c in comments if c.post_id == post.id)

        report = {
            "apply": args.apply,
            "planned_courses": TARGET_COURSES,
            "planned_chapters": TARGET_COURSES * 4,
            "planned_posts": TARGET_POSTS,
            "planned_comments": None if not args.apply else len(comments),
            "covers": len(cover_pool),
            "students": len(students),
            "course_after": db.query(Course).count() + (TARGET_COURSES if args.apply else 0),
            "post_after": db.query(CommunityPost).count() + (TARGET_POSTS if args.apply else 0),
        }

        if args.apply:
            db.add(SysConfig(config_key=MARKER, config_value=json.dumps(
                {"courses": TARGET_COURSES, "posts": TARGET_POSTS, "comments": len(comments),
                 "at": now.isoformat(),
                 "course_ids": [c.id for c in courses], "post_ids": [p.id for p in posts]},
                ensure_ascii=False),
                description="一次性演示数据批量生成标记"))
            db.commit()
            report["saved"] = True

        print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
