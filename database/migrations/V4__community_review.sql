-- =============================================================================
-- V4__community_review.sql
-- 社区广场与三级内容安全风控：作品帖子、话题挑战、互动点赞评论、举报以及多模态审核留痕
-- =============================================================================

-- 30. 社区话题与挑战赛
CREATE TABLE IF NOT EXISTS `community_topic` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '话题ID',
  `name` VARCHAR(128) NOT NULL COMMENT '话题名称: 如 #我画津门新皮影',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '话题介绍与规则',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '话题头图',
  `post_count` INT NOT NULL DEFAULT 0 COMMENT '作品累计参与数',
  `start_at` DATETIME DEFAULT NULL COMMENT '开始时间',
  `end_at` DATETIME DEFAULT NULL COMMENT '结束时间',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/CLOSED',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_topic_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区挑战话题表';

-- 25. 社区作品帖子主表
CREATE TABLE IF NOT EXISTS `community_post` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '帖子ID',
  `user_id` BIGINT NOT NULL COMMENT '作者ID',
  `title` VARCHAR(128) NOT NULL COMMENT '作品名称',
  `content` TEXT DEFAULT NULL COMMENT '创作灵感心得与非遗故事',
  `category` VARCHAR(32) NOT NULL DEFAULT 'SHADOW_PUPPET' COMMENT '所属非遗门类',
  `cover_asset_id` BIGINT DEFAULT NULL COMMENT '封面资源ID',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '封面直链快照',
  `source_task_id` CHAR(32) DEFAULT NULL COMMENT '来源AI创作任务ID',
  `topic_id` BIGINT DEFAULT NULL COMMENT '所属话题ID',
  `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING_REVIEW' COMMENT 'DRAFT/PENDING_REVIEW/APPROVED/REJECTED/OFFLINE',
  `is_featured` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否官方精选推荐',
  `is_pinned` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶',
  `heritage_master_like` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否有非遗传承人点赞认证',
  `like_count` INT NOT NULL DEFAULT 0 COMMENT '点赞数',
  `comment_count` INT NOT NULL DEFAULT 0 COMMENT '评论数',
  `favorite_count` INT NOT NULL DEFAULT 0 COMMENT '收藏数',
  `view_count` INT NOT NULL DEFAULT 0 COMMENT '浏览量',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_status_featured_created` (`status`, `is_featured`, `created_at`),
  KEY `idx_user_posts` (`user_id`, `created_at`),
  KEY `idx_topic_post` (`topic_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区作品分享主表';

-- 26. 作品多媒资图片/视频/3D模型映射表
CREATE TABLE IF NOT EXISTS `community_post_asset` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `post_id` BIGINT NOT NULL,
  `asset_id` BIGINT NOT NULL,
  `sort_no` INT NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_post_asset` (`post_id`, `sort_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作品媒资关联表';

-- 27. 社区评论表
CREATE TABLE IF NOT EXISTS `community_comment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '评论ID',
  `post_id` BIGINT NOT NULL COMMENT '所属帖子ID',
  `user_id` BIGINT NOT NULL COMMENT '评论者ID',
  `reply_to_id` BIGINT DEFAULT NULL COMMENT '父级回复评论ID',
  `content` VARCHAR(1000) NOT NULL COMMENT '评论文本内容',
  `status` VARCHAR(16) NOT NULL DEFAULT 'APPROVED' COMMENT 'PENDING_REVIEW/APPROVED/DELETED',
  `like_count` INT NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_post_comment` (`post_id`, `created_at`),
  KEY `idx_user_comment` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区作品互动评论表';

-- 28. 社区点赞表（联合唯一防刷）
CREATE TABLE IF NOT EXISTS `community_like` (
  `post_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`post_id`, `user_id`),
  KEY `idx_user_like` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区点赞关系表';

-- 29. 社区作品收藏表
CREATE TABLE IF NOT EXISTS `community_favorite` (
  `post_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`post_id`, `user_id`),
  KEY `idx_user_favorite` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区作品收藏表';

-- 31. 社区举报维权表
CREATE TABLE IF NOT EXISTS `community_report` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `post_id` BIGINT NOT NULL,
  `reporter_id` BIGINT NOT NULL,
  `reason` VARCHAR(64) NOT NULL COMMENT '涉政/涉黄/盗用/辱骂/低俗广告/其他',
  `description` VARCHAR(500) DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING/HANDLED/REJECTED',
  `handled_by` BIGINT DEFAULT NULL,
  `handled_note` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `handled_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_post_report` (`post_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社区违规举报表';

-- 32. 三级内容安全多模态审核流水表
CREATE TABLE IF NOT EXISTS `content_review` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '审核记录ID',
  `target_type` VARCHAR(32) NOT NULL DEFAULT 'COMMUNITY_POST' COMMENT 'COMMUNITY_POST/COMMENT/COURSE',
  `target_id` BIGINT NOT NULL COMMENT '审核目标实体ID',
  `risk_level` VARCHAR(16) NOT NULL DEFAULT 'LOW' COMMENT 'SAFE/LOW/MEDIUM/HIGH',
  `result` VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING/APPROVED/REJECTED/MANUAL_REVIEW',
  `ai_analysis_json` JSON DEFAULT NULL COMMENT 'AI多模态审核返回(敏感词命中, OCR文字识别, 色情暴力概率)',
  `reviewer_id` BIGINT DEFAULT NULL COMMENT '人工审核管理员ID(若二审)',
  `review_comment` VARCHAR(500) DEFAULT NULL COMMENT '审核意见与驳回原因',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `reviewed_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_target` (`target_type`, `target_id`),
  KEY `idx_result_level` (`result`, `risk_level`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多模态内容安全审核流水表';
