-- =============================================================================
-- V1__init_auth_user.sql
-- 身份与用户数据域：用户、角色、权限、画像、成长能量值与徽章
-- =============================================================================

-- 1. 用户表
CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户主键ID',
  `username` VARCHAR(64) NOT NULL COMMENT '登录名/学号/工号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '加密密码',
  `nickname` VARCHAR(64) NOT NULL COMMENT '用户昵称',
  `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像图片地址',
  `role_code` VARCHAR(32) NOT NULL DEFAULT 'STUDENT' COMMENT '主要角色: STUDENT/TEACHER/ADMIN/TOURIST',
  `grade` VARCHAR(32) DEFAULT NULL COMMENT '学段或年级: 小学低段/小学高段/初中/成人',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态: ACTIVE/DISABLED',
  `phone` VARCHAR(32) DEFAULT NULL COMMENT '手机号',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_role_status` (`role_code`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户表';

-- 2. 角色表
CREATE TABLE IF NOT EXISTS `sys_role` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `code` VARCHAR(32) NOT NULL COMMENT '角色标识',
  `name` VARCHAR(64) NOT NULL COMMENT '角色名称',
  `description` VARCHAR(255) DEFAULT NULL COMMENT '角色描述',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT '状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统角色表';

-- 3. 权限表
CREATE TABLE IF NOT EXISTS `sys_permission` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '权限ID',
  `code` VARCHAR(64) NOT NULL COMMENT '权限唯一标识',
  `name` VARCHAR(64) NOT NULL COMMENT '权限名称',
  `resource` VARCHAR(128) NOT NULL COMMENT '资源路径或前端组件标识',
  `type` VARCHAR(16) NOT NULL DEFAULT 'MENU' COMMENT '类型: MENU/BUTTON/API',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限定义表';

-- 4. 角色权限关联表
CREATE TABLE IF NOT EXISTS `sys_role_permission` (
  `role_id` BIGINT NOT NULL,
  `permission_id` BIGINT NOT NULL,
  PRIMARY KEY (`role_id`, `permission_id`),
  KEY `idx_permission_id` (`permission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色-权限关联表';

-- 5. 用户扩展画像表
CREATE TABLE IF NOT EXISTS `user_profile` (
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `school_name` VARCHAR(128) DEFAULT NULL COMMENT '所属乡村学校/单位',
  `district` VARCHAR(64) DEFAULT NULL COMMENT '所属区县: 如西青区/宝坻区/蓟州区',
  `bio` VARCHAR(255) DEFAULT NULL COMMENT '个人格言或简介',
  `avatar_config_json` JSON DEFAULT NULL COMMENT '虚拟非遗分身配置数据',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户画像与虚拟分身扩展表';

-- 6. 用户非遗兴趣标签
CREATE TABLE IF NOT EXISTS `user_interest` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `tag_code` VARCHAR(32) NOT NULL COMMENT '皮影/年画/泥人/风筝/大鼓等',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_tag` (`user_id`, `tag_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户非遗兴趣标签表';

-- 7. 用户成长能量主表
CREATE TABLE IF NOT EXISTS `user_growth` (
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `energy_value` INT NOT NULL DEFAULT 0 COMMENT '当前非遗能量值',
  `level_code` VARCHAR(32) NOT NULL DEFAULT 'LV1_APPRENTICE' COMMENT '等级: 小小学徒/匠心初成/津门小巧手等',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户成长能量主表';

-- 8. 成长能量值事件流水（防刷与幂等控制）
CREATE TABLE IF NOT EXISTS `growth_event` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `event_type` VARCHAR(32) NOT NULL COMMENT 'COURSE_FINISH/QUIZ_PASS/AI_CREATE/CHECKIN/HOMEWORK',
  `ref_id` VARCHAR(64) NOT NULL COMMENT '关联业务ID',
  `value` INT NOT NULL COMMENT '增加能量值',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_event_ref` (`user_id`, `event_type`, `ref_id`),
  KEY `idx_user_time` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='能量值事件流水表';

-- 9. 徽章规则定义表
CREATE TABLE IF NOT EXISTS `badge` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `code` VARCHAR(64) NOT NULL COMMENT '徽章标识',
  `name` VARCHAR(64) NOT NULL COMMENT '徽章名称: 如津门皮影匠人/大鼓韵声',
  `description` VARCHAR(255) NOT NULL COMMENT '解锁条件描述',
  `icon_url` VARCHAR(500) NOT NULL COMMENT '徽章图样',
  `condition_json` JSON DEFAULT NULL COMMENT '判定条件JSON',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_badge_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='徽章规则定义表';

-- 10. 用户已解锁徽章表
CREATE TABLE IF NOT EXISTS `user_badge` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `badge_id` BIGINT NOT NULL,
  `unlocked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_badge` (`user_id`, `badge_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户已解锁徽章表';

-- 11. 用户收藏表
CREATE TABLE IF NOT EXISTS `user_favorite` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `target_type` VARCHAR(32) NOT NULL COMMENT 'COURSE/POST/HERITAGE/PRODUCT',
  `target_id` BIGINT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_fav` (`user_id`, `target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏表';
