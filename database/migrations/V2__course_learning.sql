-- =============================================================================
-- V2__course_learning.sql
-- 教学与学习数据域：非遗课程、章节、媒资资源、学习进度、离线同步事件、题库与测验
-- =============================================================================

-- 12. 课程主表
CREATE TABLE IF NOT EXISTS `course` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '课程ID',
  `title` VARCHAR(128) NOT NULL COMMENT '课程标题',
  `subtitle` VARCHAR(255) DEFAULT NULL COMMENT '副标题/教学亮点',
  `category` VARCHAR(32) NOT NULL COMMENT '非遗分类: SHADOW_PUPPET(皮影)/BRONZE(青铜)/BALLAD(鼓曲)/LACQUER(漆艺)/EMBROIDERY(刺绣)/CLAY(泥人张)/PAINTING(杨柳青年画)',
  `age_group` VARCHAR(32) NOT NULL DEFAULT 'PRIMARY_LOW' COMMENT '学段: PRIMARY_LOW(低年级动画)/PRIMARY_HIGH(高年级实操)/JUNIOR(初中项目式)',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '课程封面图',
  `cover_asset_id` BIGINT DEFAULT NULL COMMENT '关联封面资源ID',
  `description` TEXT DEFAULT NULL COMMENT '课程简介与美育目标',
  `duration_minutes` INT NOT NULL DEFAULT 0 COMMENT '总时长(分钟)',
  `energy_reward` INT NOT NULL DEFAULT 50 COMMENT '学完奖励能量值',
  `view_count` INT NOT NULL DEFAULT 0 COMMENT '浏览量',
  `status` VARCHAR(16) NOT NULL DEFAULT 'PUBLISHED' COMMENT 'DRAFT/PUBLISHED/OFFLINE',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_cat_age_status` (`category`, `age_group`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='非遗课程主表';

-- 13. 课程章节表
CREATE TABLE IF NOT EXISTS `course_chapter` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '章节ID',
  `course_id` BIGINT NOT NULL COMMENT '所属课程ID',
  `seq` INT NOT NULL DEFAULT 1 COMMENT '排序章节号',
  `title` VARCHAR(128) NOT NULL COMMENT '章节标题',
  `video_url` VARCHAR(500) DEFAULT NULL COMMENT '视频CDN直链',
  `media_asset_id` BIGINT DEFAULT NULL COMMENT '关联媒资资源ID',
  `duration_seconds` INT NOT NULL DEFAULT 0 COMMENT '视频秒数',
  `key_points_json` JSON DEFAULT NULL COMMENT '本节非遗核心知识点',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_course_seq` (`course_id`, `seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程章节明细表';

-- 14. 课程讲义/教案/拓展资源表
CREATE TABLE IF NOT EXISTS `course_resource` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `course_id` BIGINT NOT NULL,
  `asset_id` BIGINT NOT NULL,
  `title` VARCHAR(128) NOT NULL COMMENT '资源名称',
  `resource_type` VARCHAR(32) NOT NULL DEFAULT 'HANDOUT' COMMENT 'HANDOUT/PPT/3D_MODEL/WORKSHEET',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_course_resource` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程配套教学资源表';

-- 15. 学生学习进度表（弱网同步目标表）
CREATE TABLE IF NOT EXISTS `learning_progress` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '学生用户ID',
  `chapter_id` BIGINT NOT NULL COMMENT '章节ID',
  `course_id` BIGINT NOT NULL COMMENT '冗余课程ID以加速查询',
  `position_seconds` INT NOT NULL DEFAULT 0 COMMENT '播放进度(秒)',
  `duration_seconds` INT NOT NULL DEFAULT 0 COMMENT '总时长(秒)',
  `completed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否完成本章节',
  `completed_at` DATETIME DEFAULT NULL COMMENT '完成时间',
  `last_learned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后学习时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_chapter` (`user_id`, `chapter_id`),
  KEY `idx_user_course` (`user_id`, `course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生学习进度记录表';

-- 16. 弱网离线事件批量同步留痕表
CREATE TABLE IF NOT EXISTS `offline_sync_event` (
  `event_id` VARCHAR(64) NOT NULL COMMENT '客户端生成的UUID事件ID',
  `user_id` BIGINT NOT NULL COMMENT '上报用户ID',
  `event_type` VARCHAR(32) NOT NULL COMMENT 'PROGRESS_UPDATE/QUIZ_SUBMIT',
  `payload_json` JSON NOT NULL COMMENT '事件完整上下文数据',
  `event_time` DATETIME NOT NULL COMMENT '客户端产生事件时的时间',
  `synced_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '服务端入库合并时间',
  PRIMARY KEY (`event_id`),
  KEY `idx_user_synced` (`user_id`, `synced_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='离线进度事件同步审计表';

-- 17. 随堂测验表
CREATE TABLE IF NOT EXISTS `quiz` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '测验ID',
  `course_id` BIGINT NOT NULL COMMENT '所属课程ID',
  `chapter_id` BIGINT DEFAULT NULL COMMENT '关联章节ID(若针对单节)',
  `title` VARCHAR(128) NOT NULL COMMENT '测验标题',
  `pass_score` INT NOT NULL DEFAULT 60 COMMENT '及格分',
  `energy_reward` INT NOT NULL DEFAULT 20 COMMENT '通关能量值',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_course_quiz` (`course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随堂测验定义表';

-- 18. 测验题目表
CREATE TABLE IF NOT EXISTS `quiz_question` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '题目ID',
  `quiz_id` BIGINT NOT NULL COMMENT '所属测验',
  `seq` INT NOT NULL DEFAULT 1 COMMENT '题号顺序',
  `type` VARCHAR(16) NOT NULL DEFAULT 'SINGLE' COMMENT 'SINGLE(单选)/MULTIPLE(多选)/JUDGE(判断)',
  `content` TEXT NOT NULL COMMENT '题干描述',
  `options_json` JSON NOT NULL COMMENT '选项列表: [{\"key\":\"A\",\"text\":\"...\"}]',
  `answer_json` JSON NOT NULL COMMENT '正确答案: [\"A\"]',
  `explanation` TEXT DEFAULT NULL COMMENT '非遗文化知识点解析',
  `score` INT NOT NULL DEFAULT 10 COMMENT '分值',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_quiz_seq` (`quiz_id`, `seq`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测验题目表';

-- 19. 学生测验作答记录表
CREATE TABLE IF NOT EXISTS `quiz_attempt` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `quiz_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `score` INT NOT NULL DEFAULT 0,
  `passed` TINYINT(1) NOT NULL DEFAULT 0,
  `answer_json` JSON NOT NULL COMMENT '学生提交选项快照',
  `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_quiz` (`user_id`, `quiz_id`, `submitted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生测验作答记录表';
