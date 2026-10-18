-- DESTRUCTIVE: back up the V11 tables and confirm before executing.
-- Application rollback can retain these additive tables without losing records.
DROP TABLE IF EXISTS class_message;
DROP TABLE IF EXISTS class_session;
DROP TABLE IF EXISTS class_attendance;
DROP TABLE IF EXISTS class_notice;
DROP TABLE IF EXISTS lesson_plan_record;
