"""Exercise forward/rollback DDL only in brand-new audit databases.

Uses the dedicated local test container, never the application database.
Audit schemas are retained for inspection; no database is deleted.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
fresh = "jinyun_audit_fresh_" + stamp
upgrade = "jinyun_audit_upgrade_" + stamp
command = ["docker", "exec", "-i", "jinyun-android-mysql", "sh", "-c",
           'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --default-character-set=utf8mb4 --batch --skip-column-names']


def sql(statement):
    result = subprocess.run(command, input=statement, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


schema = (ROOT / "database/schema_all.sql").read_text(encoding="utf-8")
assert not re.search(r"\b(DROP|TRUNCATE|USE|CREATE DATABASE)\b", schema, re.I), "Review unexpected schema operations"
for name in [fresh, upgrade]:
    assert re.fullmatch(r"jinyun_audit_(fresh|upgrade)_\d{8}_\d{6}", name)
    sql(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
sql(f"USE `{fresh}`;\n" + schema)
sql(f"USE `{fresh}`;\n" + schema)
sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/V17__course_design_badges.sql").read_text(encoding="utf-8"))
for _ in range(2):
    sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/V18__support_handling.sql").read_text(encoding="utf-8"))
    sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/V19__lesson_plan_requests.sql").read_text(encoding="utf-8"))
print("PASS: complete schema initialization and repeated initialization")
base = schema.split("-- Additive migration for the MasterGo Android client.")[0]
base = re.sub(r"^.*`client_request_id`.*\n", "", base, flags=re.M)
base = re.sub(r"^.*`(?:location_accuracy_meters|geofence_status)`.*\n", "", base, flags=re.M)
base = re.sub(r"^.*KEY `idx_user_landmark`.*\n", "", base, flags=re.M)
base = base.replace("  KEY `idx_user_checkin`", "  UNIQUE KEY `uk_user_landmark_date` (`user_id`, `landmark_id`),\n  KEY `idx_user_checkin`")
sql(f"USE `{upgrade}`;\n" + base)
forward = ["V10__mobile_client.sql", "V11__teacher_collaboration.sql", "V12__market_exchanges.sql", "V13__walking_sessions.sql", "V14__artwork_details.sql", "V15__learning_days.sql", "V16__checkin_location_accuracy.sql", "V17__course_design_badges.sql", "V18__support_handling.sql", "V19__lesson_plan_requests.sql"]
for filename in forward:
    sql(f"USE `{upgrade}`;\n" + (ROOT / "database/migrations" / filename).read_text(encoding="utf-8"))
print("PASS: V9-shaped schema upgraded through V10–V19")
fresh_columns = sql(f"SELECT CONCAT(TABLE_NAME,':',COLUMN_NAME,':',COLUMN_TYPE) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{fresh}' ORDER BY TABLE_NAME,ORDINAL_POSITION;")
upgraded_columns = sql(f"SELECT CONCAT(TABLE_NAME,':',COLUMN_NAME,':',COLUMN_TYPE) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='{upgrade}' ORDER BY TABLE_NAME,ORDINAL_POSITION;")
# ALTER appends the order idempotency column, so compare independent of physical column order.
assert set(fresh_columns.splitlines()) == set(upgraded_columns.splitlines()), "Fresh and upgraded columns differ"
print("PASS: fresh and upgraded table columns match")
for name in [fresh, upgrade]:
    indexes = sql(f"SELECT CONCAT(INDEX_NAME,':',NON_UNIQUE) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='{name}' AND TABLE_NAME='activity_checkin';")
    assert 'uk_user_landmark_date:' not in indexes and 'idx_user_landmark:1' in indexes, indexes
print("PASS: repeat visits use a non-unique lookup index")
for name in [fresh, upgrade]:
    indexes = sql(f"SELECT CONCAT(INDEX_NAME,':',NON_UNIQUE) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='{name}' AND TABLE_NAME='user_badge';")
    assert 'uk_user_badge:0' in indexes, indexes
print("PASS: badge awards have a unique user/badge constraint")
sql(f"USE `{fresh}`;\n" + """
INSERT INTO user_feedback (id,user_id,content,status,reply_text,handled_by,handled_at)
VALUES (9101,9001,'keep feedback','RESOLVED','keep reply',1,'2020-01-01 00:00:00');
INSERT INTO energy_exchange (id,request_id,user_id,item_id,item_name,energy_cost,receiver_name,receiver_phone,receiver_address,status,tracking_no,handling_note,handled_by,handled_at)
VALUES (9101,'audit-support',9001,9001,'audit item',20,'audit','100000','audit address','FULFILLED','audit receipt','keep note',1,'2020-01-01 00:00:00');
""")
sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/rollback/V18__support_handling.sql").read_text(encoding="utf-8"))
for _ in range(2):
    sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/V18__support_handling.sql").read_text(encoding="utf-8"))
assert sql(f"SELECT CONCAT(content,':',reply_text,':',handled_by,':',handled_at) FROM `{fresh}`.user_feedback WHERE id=9101;") == 'keep feedback:keep reply:1:2020-01-01 00:00:00'
assert sql(f"SELECT CONCAT(tracking_no,':',handling_note,':',handled_by,':',handled_at) FROM `{fresh}`.energy_exchange WHERE id=9101;") == 'audit receipt:keep note:1:2020-01-01 00:00:00'
print("PASS: support replies and exchange handling survive V18 repeat and code rollback")
sql(f"USE `{fresh}`;\n" + """
INSERT INTO lesson_plan_record (id,teacher_id,title,grade,topic,duration_minutes,content_json,source,request_id,request_mode)
VALUES (9101,9001,'keep lesson','grade','topic',45,'{}','keep source','audit-plan-1','LOCAL'),
       (9103,9001,'legacy one','grade','topic',45,'{}','keep source',NULL,NULL),
       (9104,9001,'legacy two','grade','topic',45,'{}','keep source',NULL,NULL),
       (9105,9002,'another teacher','grade','topic',45,'{}','keep source','audit-plan-1','LOCAL');
""")
try:
    sql(f"INSERT INTO `{fresh}`.lesson_plan_record (teacher_id,title,grade,topic,duration_minutes,content_json,source,request_id) VALUES (9001,'duplicate','grade','topic',45,'{{}}','source','audit-plan-1');")
    raise AssertionError("Duplicate teacher/request identity was accepted")
except RuntimeError as error:
    assert "Duplicate entry" in str(error)
sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/rollback/V19__lesson_plan_requests.sql").read_text(encoding="utf-8"))
for _ in range(2):
    sql(f"USE `{fresh}`;\n" + (ROOT / "database/migrations/V19__lesson_plan_requests.sql").read_text(encoding="utf-8"))
assert sql(f"SELECT CONCAT(title,':',source,':',request_id,':',request_mode) FROM `{fresh}`.lesson_plan_record WHERE id=9101;") == 'keep lesson:keep source:audit-plan-1:LOCAL'
assert sql(f"SELECT COUNT(*) FROM `{fresh}`.lesson_plan_record;") == '4'
print("PASS: V19 repeat/code rollback preserves lessons, nullable legacy identities and per-teacher request uniqueness")
for filename in reversed(forward):
    sql(f"USE `{upgrade}`;\n" + (ROOT / "database/migrations/rollback" / filename).read_text(encoding="utf-8"))
print("PASS: rollback V19–V10 retains badge catalog and removes the empty feature schema")
for filename in forward:
    sql(f"USE `{upgrade}`;\n" + (ROOT / "database/migrations" / filename).read_text(encoding="utf-8"))
print("PASS: forward migrations apply again after rollback")
sql(f"USE `{upgrade}`;\n" + """
INSERT INTO learning_progress (user_id, chapter_id, course_id, position_seconds, duration_seconds, completed, completed_at, last_learned_at)
VALUES (9001, 9001, 9001, 20, 60, 1, '2020-01-01 15:00:00', '2020-01-02 16:30:00'),
       (9002, 9002, 9001, 0, 60, 0, NULL, '2020-01-04 00:00:00');
INSERT INTO offline_sync_event (event_id, user_id, event_type, payload_json, event_time)
VALUES ('audit-learning-day', 9001, 'PROGRESS_UPDATE', '{"position_seconds":10,"completed":false}', '2020-01-02 15:30:00'),
       ('audit-zero-day', 9002, 'PROGRESS_UPDATE', '{"position_seconds":0,"completed":false}', '2020-01-04 00:00:00');
INSERT INTO learning_day (user_id, day, created_at) VALUES (9003, '2020-01-04', UTC_TIMESTAMP());
""")
for _ in range(2):
    sql(f"USE `{upgrade}`;\n" + (ROOT / "database/migrations/V15__learning_days.sql").read_text(encoding="utf-8"))
days = sql(f"SELECT CONCAT(user_id,':',day) FROM `{upgrade}`.learning_day ORDER BY user_id,day;")
assert days.splitlines() == ["9001:2020-01-01", "9001:2020-01-02", "9001:2020-01-03", "9003:2020-01-04"], days
print("PASS: Shanghai-date history backfill is repeatable and preserves existing days")
sql(f"USE `{upgrade}`;\n" + """
INSERT INTO sys_user (id, username, password_hash, nickname) VALUES
(9010, 'audit-badge-complete', 'not-a-login', 'audit'), (9011, 'audit-badge-partial', 'not-a-login', 'audit');
INSERT INTO course (id, title, category, status) VALUES
(9010, 'audit bronze', 'BRONZE', 'PUBLISHED'), (9011, 'audit empty', 'PAPER_CUTTING', 'PUBLISHED');
INSERT INTO course_chapter (id, course_id, title) VALUES (9010,9010,'chapter one'), (9011,9010,'chapter two');
INSERT INTO learning_progress (user_id,chapter_id,course_id,completed) VALUES
(9010,9010,9010,1), (9010,9011,9010,1), (9011,9010,9010,1);
UPDATE badge SET description='preserve administrator text' WHERE code='BADGE_COURSE_BRONZE';
""")
for _ in range(2):
    sql(f"USE `{upgrade}`;\n" + (ROOT / "database/migrations/V17__course_design_badges.sql").read_text(encoding="utf-8"))
awards = sql(f"SELECT CONCAT(ub.user_id,':',b.code) FROM `{upgrade}`.user_badge ub JOIN `{upgrade}`.badge b ON b.id=ub.badge_id ORDER BY ub.user_id;")
assert awards.splitlines() == ['9010:BADGE_COURSE_BRONZE'], awards
assert sql(f"SELECT description FROM `{upgrade}`.badge WHERE code='BADGE_COURSE_BRONZE';") == 'preserve administrator text'
assert sql(f"SELECT COUNT(*) FROM `{upgrade}`.badge;") == '7'
print("PASS: course badge backfill is repeatable, excludes partial/empty courses and preserves edited catalog")
report = {"fresh_schema":fresh,"upgrade_schema":upgrade,"checks":["fresh initialization","repeat initialization","V10–V19 upgrade","column parity","badge unique constraint","V18 reply and handling preservation on repeat/rollback","V19 lesson/request preservation, legacy NULLs and per-teacher uniqueness","empty-feature-schema rollback retaining badges","reapply","learning-date backfill and repeat","course-badge backfill and repeat"],"retained":True}
destination = ROOT / ".local/android/migration-audit.json"
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("Audit schemas retained; report: .local/android/migration-audit.json")
