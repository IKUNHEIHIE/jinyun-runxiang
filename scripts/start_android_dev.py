"""Run from WSL with the isolated project Python environment.

Creates a dedicated development MySQL volume; never resets existing data.
Credentials stay in ignored .local/android/ with mode 0600.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local" / "android"
LOCAL.mkdir(parents=True, exist_ok=True)


def private_json(path, factory):
    if path.exists():
        return json.loads(path.read_text())
    value = factory()
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    path.chmod(0o600)
    return value


def bootstrap():
    credentials = private_json(LOCAL / "credentials.json", lambda: {
        "mysql_root": secrets.token_urlsafe(32), "mysql_password": secrets.token_urlsafe(32),
        "jwt": secrets.token_urlsafe(48),
        "users": {name: secrets.token_urlsafe(18) for name in ["student_demo", "teacher_demo", "admin_demo"]},
    })
    mysql_env = LOCAL / "mysql.env"
    mysql_env.write_text("\n".join(["MYSQL_DATABASE=jinyun_android_dev", "MYSQL_USER=jinyun_android",
                                    "MYSQL_PASSWORD=" + credentials["mysql_password"],
                                    "MYSQL_ROOT_PASSWORD=" + credentials["mysql_root"]]))
    mysql_env.chmod(0o600)
    exists = subprocess.run(["docker", "container", "inspect", "jinyun-android-mysql"], capture_output=True).returncode == 0
    if not exists:
        subprocess.run(["docker", "run", "-d", "--name", "jinyun-android-mysql", "--env-file", str(mysql_env),
                        "-p", "127.0.0.1:13306:3306", "-v", "jinyun_android_mysql_data:/var/lib/mysql", "mysql:8.0"], check=True)
    else:
        subprocess.run(["docker", "start", "jinyun-android-mysql"], check=True, stdout=subprocess.DEVNULL)
    env = {"DATABASE_URL": "mysql+pymysql://jinyun_android:" + credentials["mysql_password"] + "@127.0.0.1:13306/jinyun_android_dev",
           "JWT_SECRET_KEY": credentials["jwt"], "MYSQL_SOCKET": "", "PYTHONPATH": str(ROOT / "backend"),
           "ALLOWED_ORIGINS": "https://localhost,http://localhost,http://localhost:5174,http://127.0.0.1:5174"}
    backend_env = LOCAL / "backend.env"
    backend_env.write_text("\n".join(f"{k}={v}" for k, v in env.items()))
    backend_env.chmod(0o600)
    os.environ.update(env)
    sys.path.insert(0, str(ROOT / "backend"))
    from sqlalchemy import text, inspect
    from app.core.database import Base, SessionLocal, engine
    from app.models import entities, mobile
    from app.core.security import hash_password
    from app.models.entities import SysUser, UserProfile, UserGrowth, Course, CourseChapter, Quiz, QuizQuestion, TeacherClass, ClassMember
    from app.models.mobile import HeritageEntry
    for attempt in range(60):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception:
            if attempt == 59:
                raise RuntimeError("Development MySQL did not become ready") from None
            time.sleep(1)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        support_migration = (ROOT / "database/migrations/V18__support_handling.sql").read_text(encoding="utf-8")
        for statement in support_migration.split(';'):
            if statement.strip():
                connection.execute(text(statement))
        lesson_migration = (ROOT / "database/migrations/V19__lesson_plan_requests.sql").read_text(encoding="utf-8")
        for statement in lesson_migration.split(';'):
            if statement.strip():
                connection.execute(text(statement))
        contest_migration = (ROOT / "database/migrations/V20__class_contests.sql").read_text(encoding="utf-8")
        for statement in contest_migration.split(';'):
            if statement.strip():
                connection.execute(text(statement))
    if "uk_user_badge" not in {i["name"] for i in inspect(engine).get_indexes("user_badge")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE user_badge ADD UNIQUE KEY uk_user_badge (user_id, badge_id)"))
    checkin_columns = {c["name"] for c in inspect(engine).get_columns("activity_checkin")}
    for column, definition in [("location_accuracy_meters", "DECIMAL(10,2) NULL"), ("geofence_status", "VARCHAR(16) NULL")]:
        if column not in checkin_columns:
            with engine.begin() as connection:
                connection.execute(text(f"ALTER TABLE activity_checkin ADD COLUMN {column} {definition}"))
    checkin_indexes = {i["name"] for i in inspect(engine).get_indexes("activity_checkin")}
    with engine.begin() as connection:
        if "uk_user_landmark_date" in checkin_indexes:
            connection.execute(text("ALTER TABLE activity_checkin DROP INDEX uk_user_landmark_date"))
        if "idx_user_landmark" not in checkin_indexes:
            connection.execute(text("ALTER TABLE activity_checkin ADD INDEX idx_user_landmark (user_id, landmark_id)"))
    with engine.begin() as connection:
        migration = (ROOT / "database/migrations/V15__learning_days.sql").read_text(encoding="utf-8")
        for statement in migration.split(";"):
            if statement.strip():
                connection.execute(text(statement))
    if "client_request_id" not in {c["name"] for c in inspect(engine).get_columns("order_main")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE order_main ADD COLUMN client_request_id VARCHAR(64) NULL, ADD UNIQUE KEY uk_order_client_request_id (client_request_id)"))
    assets = json.loads((ROOT / "user-web/src/mobile/design-assets.json").read_text())
    destination = ROOT / "backend/static/design"
    destination.mkdir(exist_ok=True)
    def image(screen, node):
        url = assets[screen]["images"][node]
        source = ROOT / "user-web/public" / url.lstrip("/")
        target = destination / source.name
        if not target.exists():
            shutil.copy2(source, target)
        return "/static/design/" + source.name

    def heritage_content(title, summary):
        content = {"sections": [{"title": "基本信息", "body": summary}],
                   "source": "MasterGo 设计稿内容，开发环境初始条目"}
        if title == "后母戊鼎":
            content["metrics"] = [{"label": "高度", "value": "133.0 cm"},
                                  {"label": "口长", "value": "110.0 cm"},
                                  {"label": "口宽", "value": "79.0 cm"},
                                  {"label": "重量", "value": "832.84 kg"}]
        if title != "杨柳青年画":
            return content
        return {
            "source": "MasterGo 40:32809 设计稿内容，开发环境示例条目",
            "hero_url": "/design/images/1d096953210d426fc2ef3300764b80a3.webp",
            "sections": [
                {
                    "eyebrow": "CLASSIC THEMES", "title": "经典题材",
                    "body": "杨柳青年画以“娃娃、戏曲、花卉”为经典题材，寄托人们对美好生活的向往。",
                    "items": [
                        {"badge": "最受欢迎", "title": "娃娃类题材", "subtitle": "连年有余 · 五谷丰登 · 麒麟送子",
                         "body": "胖娃娃是杨柳青年画最具代表性的题材。娃娃或怀抱鲤鱼寓意“连年有余”，或手捧谷穗象征“五谷丰登”。",
                         "image_url": "/design/images/4e56134e7d2a8d417862b43ca1ba1161.png"},
                        {"title": "戏曲故事", "subtitle": "京剧 · 评剧",
                         "body": "取材于京剧、评剧等经典剧目，如《白蛇传》《西游记》《三国演义》等，人物形象生动，情节引人入胜。",
                         "image_url": "/design/images/6c315b81dd6dfeb3b254b58c6798c9b5.png"},
                        {"title": "风景花卉", "subtitle": "四时花卉 · 文人画",
                         "body": "四时花卉与山水风景，梅、兰、竹、菊寓意高洁品格，配以诗词题跋，兼具文人意趣。",
                         "image_url": "/design/images/0b40a6c09937d62155b834be8bb295bb.png"},
                    ],
                },
                {
                    "eyebrow": "CRAFTSMANSHIP", "title": "半印半画",
                    "body": "木版套印与手工彩绘的完美结合。",
                    "steps": [
                        {"title": "勾描刻版", "body": "画师将画稿反贴在梨木板上，以工笔勾描，再由刻工运用“发、衬、挑、复、剔”等刀法精雕细刻，形成墨线版。"},
                        {"title": "木版套印", "body": "采用“饾版”水印技术，将墨线版与色版分次套印。一版一色，层层叠加，要求“版版精准、色色分明”。"},
                        {"title": "手工彩绘", "body": "套印完成后，画师以“开脸”“勾金”“晕染”等技法手工彩绘。人物面部“三白九染”，服饰纹样精细勾勒，赋予作品独特生命力。"},
                        {"title": "装裱成品", "body": "经过托裱、裁切、装框等工序，一幅完整的杨柳青年画方才诞生。“半印半画”的独特工艺，使其兼具版画的力度与手绘的灵动。"},
                    ],
                },
                {
                    "eyebrow": "ORIGIN & HISTORY", "title": "源起",
                    "body": "杨柳青年画发源于明代崇祯年间，盛于清代乾隆嘉庆时期，因产于天津杨柳青镇而得名。",
                    "image_url": "/design/images/dfb7e1bc3c668957a1b76b3f2be77948.png",
                    "timeline": [
                        {"era": "明", "date": "崇祯年间", "title": "起源", "body": "杨柳青年画发源于明代崇祯年间，在津西杨柳青镇形成作坊式生产。"},
                        {"era": "清", "date": "乾隆嘉庆", "title": "鼎盛", "body": "清代乾隆、嘉庆时期进入鼎盛，画坊林立，作品远销各地。"},
                        {"era": "今", "date": "2006年", "title": "列入非遗", "body": "2006年列入首批国家级非物质文化遗产名录，古老技艺在当代继续传承。"},
                    ],
                },
                {
                    "eyebrow": "ARTISTIC FEATURES", "title": "艺术特色",
                    "body": "妙笔生花：色彩、线条与构图共同构成杨柳青年画的独特面貌。",
                    "features": [
                        {"title": "色彩鲜艳明快", "body": "采用朱红、石青、藤黄、花青等传统矿物颜料，色彩对比强烈而和谐，历经百年不褪色。"},
                        {"title": "线条流畅细腻", "body": "继承工笔重彩传统，线条刚柔并济、疏密有致。人物衣纹飘逸灵动，面部刻画精细入微。"},
                        {"title": "构图饱满匀称", "body": "画面布局主次分明、繁而不乱，讲究“满”与“空”的辩证统一，在丰满的构图中留出呼吸空间。"},
                    ],
                    "quote": {"text": "杨柳青年画，色彩鲜艳而不俗，构图饱满而不乱，线条流畅而有力，实为民间艺术之瑰宝。",
                              "source": "民间艺术评论"},
                },
                {
                    "eyebrow": "CULTURAL HERITAGE", "title": "传承",
                    "body": "守护传统 · 传承匠心 · 绽放新彩。",
                    "image_url": "/design/images/1d096953210d426fc2ef3300764b80a3.webp",
                    "features": [
                        {"title": "文化价值", "body": "杨柳青年画是中国北方民俗文化的百科全书，记录了数百年的社会生活、民间信仰与审美趣味。"},
                        {"title": "传承意义", "body": "2006年列入首批国家级非物质文化遗产名录。在数字化时代，杨柳青年画正以新的形式走进现代生活。"},
                        {"title": "当代创新", "body": "当代艺术家将杨柳青年画元素融入文创产品、数字艺术、时尚设计等领域，让这一古老艺术在新时代绽放异彩。"},
                    ],
                },
            ],
        }

    with SessionLocal() as db:
        users = {}
        for username, role, nickname in [("student_demo", "STUDENT", "林锦"), ("teacher_demo", "TEACHER", "张新"), ("admin_demo", "ADMIN", "开发管理员")]:
            user = db.query(SysUser).filter_by(username=username).first()
            if not user:
                user = SysUser(username=username, role_code=role, nickname=nickname,
                               password_hash=hash_password(credentials["users"][username]), grade="小学三年级")
                db.add(user); db.flush()
                db.add(UserProfile(user_id=user.id, bio="开发环境测试账号"))
                db.add(UserGrowth(user_id=user.id, energy_value=100))
            users[role] = user
        heritage = [
            ("穆桂英挂帅", "CLAY_FIGURINE", "泥人张 · 彩塑", "home", "5:01951", "津门彩塑，塑造戏曲人物神韵。"),
            ("沙燕风筝", "KITE", "潍坊 · 纸鸢", "home", "5:01989", "传统纸鸢，感受风筝的造型与色彩之美。"),
            ("连年有余", "NEW_YEAR_PAINTING", "杨柳青 · 年画", "home", "5:01977", "胖娃娃怀抱鲤鱼寓意连年有余，寄托人们对美好生活的向往。"),
            ("杨柳青年画", "NEW_YEAR_PAINTING", "始于明代 · 盛于清代", "home", "5:01977", "木版套印与手工彩绘的完美结合，传承四百余年的民间艺术。"),
            ("后母戊鼎", "BRONZE", "商代晚期", "layer-40-32808", "5:6523", "出土于河南安阳殷墟，现藏中国国家博物馆。"),
        ]
        for title, category, era, screen, node, summary in heritage:
            existing = db.query(HeritageEntry).filter_by(title=title).first()
            if not existing:
                db.add(HeritageEntry(title=title, category=category, era=era, summary=summary,
                                     cover_url=image(screen, node),
                                     content_json=heritage_content(title, summary)))
            elif title == "杨柳青年画" and (existing.content_json or {}).get("source") == "MasterGo 设计稿内容，开发环境初始条目":
                existing.content_json = heritage_content(title, summary)
        courses = [
            ("皮影艺术入门", "SHADOW_PUPPET", "home", "5:02306", 60),
            ("剪纸技艺传承", "PAPER_CUTTING", "home", "5:02116", 45),
            ("青花瓷韵", "CERAMICS", "home", "5:02185", 90),
            ("津韵服饰", "EMBROIDERY", "home", "5:02294", 60),
            ("中国传统剪纸艺术入门", "PAPER_CUTTING", "layer-40-32392", "5:05573", 45),
            ("苏绣基础针法教程", "EMBROIDERY", "layer-40-32392", "5:05384", 45),
        ]
        for title, category, screen, node, duration in courses:
            if not db.query(Course).filter_by(title=title).first():
                course = Course(title=title, category=category, age_group="PRIMARY_LOW", duration_minutes=duration,
                                subtitle="传承千年技艺，点亮文化之光", cover_url=image(screen, node),
                                description="开发环境课程内容。正式教学视频需由教师或管理员上传，未上传时界面明确显示空状态。")
                db.add(course); db.flush()
                db.add(CourseChapter(course_id=course.id, seq=1, title="认识传统工艺", duration_seconds=60,
                                     key_points_json=["观察造型", "记录色彩", "理解传承"]))
                quiz = Quiz(course_id=course.id, title="随堂 · 鉴宝", pass_score=10, energy_reward=10)
                db.add(quiz); db.flush()
                db.add(QuizQuestion(quiz_id=quiz.id, content="学习传统非遗技艺时，哪种做法有助于传承？",
                                    options_json=[{"key": "A", "text": "观察传统工艺并记录学习心得"}, {"key": "B", "text": "忽略技艺的文化背景"}],
                                    answer_json=["A"], explanation="通过观察与记录理解非遗技艺及其文化背景。", score=10))
        if not db.query(TeacherClass).filter_by(invite_code="JINYUN26").first():
            classroom = TeacherClass(teacher_id=users["TEACHER"].id, name="传统工艺研习社", grade="小学三年级", invite_code="JINYUN26")
            db.add(classroom); db.flush()
            db.add(ClassMember(class_id=classroom.id, student_id=users["STUDENT"].id))
        from dev_catalog import seed_catalog
        seed_catalog(db, image)
        db.commit()
    print("Isolated development database ready; credentials: .local/android/credentials.json")
    return env


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    env = bootstrap()
    if args.serve:
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                       cwd=ROOT / "backend", env={**os.environ, **env}, check=True)
