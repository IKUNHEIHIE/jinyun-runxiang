-- Class-vs-class contests. Additive only, existing assignments unchanged.
SET @contest_ddl = IF(EXISTS(SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='assignment' AND COLUMN_NAME='contest_id'), 'SELECT 1', 'ALTER TABLE assignment ADD COLUMN contest_id BIGINT NULL COMMENT ''所属对抗赛ID''');
PREPARE contest_change FROM @contest_ddl;
EXECUTE contest_change;
DEALLOCATE PREPARE contest_change;

SET @contest_ddl = IF(EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='assignment' AND INDEX_NAME='idx_assignment_contest'), 'SELECT 1', 'ALTER TABLE assignment ADD INDEX idx_assignment_contest (contest_id)');
PREPARE contest_change FROM @contest_ddl;
EXECUTE contest_change;
DEALLOCATE PREPARE contest_change;

CREATE TABLE IF NOT EXISTS `contest` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `teacher_id` BIGINT NOT NULL COMMENT '组织教师',
  `title` VARCHAR(128) NOT NULL COMMENT '轮次标题',
  `description` TEXT NOT NULL COMMENT '比赛任务要求',
  `tool_type` VARCHAR(32) DEFAULT NULL COMMENT '限定创作工具',
  `home_class_id` BIGINT NOT NULL,
  `away_class_id` BIGINT NOT NULL,
  `home_assignment_id` BIGINT DEFAULT NULL,
  `away_assignment_id` BIGINT DEFAULT NULL,
  `round_no` INT NOT NULL DEFAULT 1 COMMENT '轮次序号',
  `scoring_mode` VARCHAR(16) NOT NULL DEFAULT 'TOTAL' COMMENT 'TOTAL/AVERAGE',
  `deadline` DATETIME NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'OPEN' COMMENT 'OPEN/SCORING/PUBLISHED',
  `result_json` JSON DEFAULT NULL COMMENT '公布时的成绩快照',
  `published_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_contest_teacher_status` (`teacher_id`, `status`),
  KEY `idx_contest_classes` (`home_class_id`, `away_class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级对抗赛';

CREATE TABLE IF NOT EXISTS `contest_entry` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `contest_id` BIGINT NOT NULL,
  `class_id` BIGINT NOT NULL,
  `student_id` BIGINT NOT NULL,
  `assignment_id` BIGINT NOT NULL COMMENT '该学生所在班级侧的作业ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_contest_student` (`contest_id`, `student_id`),
  KEY `idx_contest_entry_student` (`student_id`),
  KEY `idx_contest_entry_contest_class` (`contest_id`, `class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对抗赛参赛名单';
