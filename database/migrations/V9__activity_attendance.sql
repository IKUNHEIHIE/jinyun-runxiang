-- Activity attendance is independent of the discontinued landmark/map check-in.
-- Run once after V6 on databases created before this change.
ALTER TABLE `activity`
  ADD COLUMN `checkin_code_hash` VARCHAR(255) DEFAULT NULL COMMENT '现场签到码的单向哈希',
  ADD COLUMN `badge_id` BIGINT DEFAULT NULL COMMENT '完成签到可发放的徽章';

CREATE TABLE IF NOT EXISTS `activity_attendance` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `activity_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `checked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_activity_attendee` (`activity_id`, `user_id`),
  KEY `idx_attendee_checked` (`user_id`, `checked_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动现场签到记录';
