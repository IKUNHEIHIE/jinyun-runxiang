-- Refresh-token rotation and server-side logout for new login sessions.
CREATE TABLE IF NOT EXISTS `auth_session` (
  `session_id` VARCHAR(36) NOT NULL,
  `user_id` BIGINT NOT NULL,
  `refresh_hash` VARCHAR(64) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `revoked_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`session_id`),
  KEY `idx_auth_user` (`user_id`, `expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户登录会话与刷新令牌';
