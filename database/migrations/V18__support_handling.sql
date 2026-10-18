-- Additive and repeatable support handling fields. Never invent historical actors or dates.
-- Keep these columns when rolling application code back. Old records remain readable.
SET @support_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='user_feedback' AND COLUMN_NAME='reply_text'), 'SELECT 1', 'ALTER TABLE user_feedback ADD COLUMN reply_text TEXT NULL');
PREPARE support_change FROM @support_ddl;
EXECUTE support_change;
DEALLOCATE PREPARE support_change;

SET @support_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='user_feedback' AND COLUMN_NAME='handled_by'), 'SELECT 1', 'ALTER TABLE user_feedback ADD COLUMN handled_by BIGINT NULL');
PREPARE support_change FROM @support_ddl;
EXECUTE support_change;
DEALLOCATE PREPARE support_change;

SET @support_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='user_feedback' AND COLUMN_NAME='handled_at'), 'SELECT 1', 'ALTER TABLE user_feedback ADD COLUMN handled_at DATETIME NULL');
PREPARE support_change FROM @support_ddl;
EXECUTE support_change;
DEALLOCATE PREPARE support_change;

SET @support_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='energy_exchange' AND COLUMN_NAME='handling_note'), 'SELECT 1', 'ALTER TABLE energy_exchange ADD COLUMN handling_note VARCHAR(500) NOT NULL DEFAULT ''''');
PREPARE support_change FROM @support_ddl;
EXECUTE support_change;
DEALLOCATE PREPARE support_change;

SET @support_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='energy_exchange' AND COLUMN_NAME='handled_by'), 'SELECT 1', 'ALTER TABLE energy_exchange ADD COLUMN handled_by BIGINT NULL');
PREPARE support_change FROM @support_ddl;
EXECUTE support_change;
DEALLOCATE PREPARE support_change;

SET @support_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='energy_exchange' AND COLUMN_NAME='handled_at'), 'SELECT 1', 'ALTER TABLE energy_exchange ADD COLUMN handled_at DATETIME NULL');
PREPARE support_change FROM @support_ddl;
EXECUTE support_change;
DEALLOCATE PREPARE support_change;
