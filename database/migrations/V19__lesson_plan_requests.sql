-- Additive request identity for saved lessons. Existing records retain NULL identities.
SET @lesson_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='lesson_plan_record' AND COLUMN_NAME='request_id'), 'SELECT 1', 'ALTER TABLE lesson_plan_record ADD COLUMN request_id VARCHAR(64) NULL');
PREPARE lesson_change FROM @lesson_ddl;
EXECUTE lesson_change;
DEALLOCATE PREPARE lesson_change;

SET @lesson_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='lesson_plan_record' AND COLUMN_NAME='request_mode'), 'SELECT 1', 'ALTER TABLE lesson_plan_record ADD COLUMN request_mode VARCHAR(16) NULL');
PREPARE lesson_change FROM @lesson_ddl;
EXECUTE lesson_change;
DEALLOCATE PREPARE lesson_change;

SET @lesson_ddl = IF(EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='lesson_plan_record' AND INDEX_NAME='uk_lesson_plan_request'), 'SELECT 1', 'ALTER TABLE lesson_plan_record ADD UNIQUE KEY uk_lesson_plan_request (teacher_id,request_id)');
PREPARE lesson_change FROM @lesson_ddl;
EXECUTE lesson_change;
DEALLOCATE PREPARE lesson_change;
