"""Generate the additive V11 DDL from the new teacher models; does not access a DB."""
import os
import secrets
import sys
from pathlib import Path
os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(48))
os.environ["DATABASE_URL"] = "sqlite://"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import mysql
from app.models.mobile import LessonPlanRecord, ClassNotice, ClassAttendance, ClassSession, ClassMessage

models = [LessonPlanRecord, ClassNotice, ClassAttendance, ClassSession, ClassMessage]
ddl = "-- V11: additive teacher collaboration tables. Apply after V10.\n"
target = ROOT / "database/migrations/V11__teacher_collaboration.sql"
old_ddl = target.read_text(encoding="utf-8") if target.exists() else ""
for model in models:
    table = model.__table__
    statement = str(CreateTable(table, if_not_exists=True).compile(dialect=mysql.dialect())).strip()
    indexes = ["INDEX " + index.name + " (" + ", ".join(c.name for c in index.columns) + ")" for index in sorted(table.indexes, key=lambda i: i.name)]
    if indexes:
        closing = statement.rfind(")")
        statement = statement[:closing].rstrip() + ",\n\t" + ",\n\t".join(indexes) + "\n)"
    statement = "\n".join(line.rstrip() for line in statement.splitlines())
    ddl += statement + " CHARACTER SET utf8mb4;\n\n"
target.write_text(ddl, encoding="utf-8")
schema = ROOT / "database/schema_all.sql"
existing = schema.read_text(encoding="utf-8")
if old_ddl and old_ddl in existing:
    schema.write_text(existing.replace(old_ddl, ddl, 1).rstrip() + "\n", encoding="utf-8")
elif not all("CREATE TABLE IF NOT EXISTS " + m.__tablename__ + " (" in existing for m in models):
    schema.write_text(existing + "\n" + ddl, encoding="utf-8")
rollback = "-- DESTRUCTIVE: back up the V11 tables and confirm before executing.\n-- Application rollback can retain these additive tables without losing records.\n"
rollback += "\n".join("DROP TABLE IF EXISTS " + m.__tablename__ + ";" for m in reversed(models)) + "\n"
(ROOT / "database/migrations/rollback/V11__teacher_collaboration.sql").write_text(rollback, encoding="utf-8")
print("V11 forward and rollback SQL written. No database was modified.")
