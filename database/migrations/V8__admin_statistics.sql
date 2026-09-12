-- =============================================================================
-- V8__admin_statistics.sql
-- 运营管控与数据分析域：非遗图文百科、轮播图、民俗节日专题、系统参数、操作审计与日运营统计看板
-- =============================================================================

-- 55. 统一图文百科与内容资讯
CREATE TABLE IF NOT EXISTS `content_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '内容ID',
  `title` VARCHAR(128) NOT NULL COMMENT '内容标题: 如 泥人张彩塑两百年技艺传承',
  `type` VARCHAR(32) NOT NULL DEFAULT 'ENCYCLOPEDIA' COMMENT 'ENCYCLOPEDIA(非遗百科)/NEWS(乡村快讯)/NOTICE(平台公告)',
  `category` VARCHAR(32) NOT NULL DEFAULT 'HERITAGE_HISTORY' COMMENT '分类',
  `summary` VARCHAR(500) DEFAULT NULL,
  `content` LONGTEXT NOT NULL COMMENT 'Markdown/HTML富文本内容',
  `cover_url` VARCHAR(500) DEFAULT NULL,
  `author` VARCHAR(64) DEFAULT '津韵润乡编辑部',
  `view_count` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(16) NOT NULL DEFAULT 'PUBLISHED' COMMENT 'DRAFT/PUBLISHED/ARCHIVED',
  `sort_no` INT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_type_status` (`type`, `status`, `sort_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='图文百科与平台资讯表';

-- 56. 首页轮播位推荐配置
CREATE TABLE IF NOT EXISTS `banner_config` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(128) NOT NULL COMMENT '轮播主题: 如 天津皮影老匠人双师直播',
  `image_url` VARCHAR(500) NOT NULL COMMENT '轮播大图',
  `link_url` VARCHAR(500) DEFAULT NULL COMMENT '跳转链接: 内部路由如 /course/1 或外部H5',
  `position` VARCHAR(32) NOT NULL DEFAULT 'HOME_TOP' COMMENT '投放位置: HOME_TOP/WORKSHOP_TOP/COMMUNITY_TOP',
  `sort_no` INT NOT NULL DEFAULT 1,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/INACTIVE',
  `start_at` DATETIME DEFAULT NULL,
  `end_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pos_status` (`position`, `status`, `sort_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='首页与频道轮播配置表';

-- 57. 天津民俗日历与节日专题
CREATE TABLE IF NOT EXISTS `festival_topic` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(128) NOT NULL COMMENT '节日名称: 如 妈祖文化节/杨柳青元宵灯会/二月二龙抬头',
  `festival_date` VARCHAR(32) NOT NULL COMMENT '农历或公历日期标记: 如 农历正月十五',
  `description` TEXT NOT NULL COMMENT '天津特色民俗文化背景',
  `custom_culture` VARCHAR(255) DEFAULT NULL COMMENT '特色风俗: 逛庙会/吃焖子/贴年画',
  `cover_url` VARCHAR(500) DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='天津民俗节日专题表';

-- 58. 模型运行时注册表（运营动态调优）
CREATE TABLE IF NOT EXISTS `model_registry` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `model_code` VARCHAR(64) NOT NULL,
  `name` VARCHAR(128) NOT NULL,
  `version` VARCHAR(32) NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/TESTING/OFFLINE',
  `description` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_reg_code` (`model_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='运营模型运行时注册表';

-- 59. 模型动态推理参数表
CREATE TABLE IF NOT EXISTS `model_parameter` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `model_id` BIGINT NOT NULL,
  `param_key` VARCHAR(64) NOT NULL COMMENT 'step, cfg, denoise, width, height, temperature',
  `param_value` VARCHAR(255) NOT NULL,
  `description` VARCHAR(255) DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_model_param` (`model_id`, `param_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型动态参数表';

-- 60. 敏感业务与合规操作审计日志
CREATE TABLE IF NOT EXISTS `audit_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '操作人ID',
  `role_code` VARCHAR(32) DEFAULT NULL,
  `action` VARCHAR(64) NOT NULL COMMENT 'LOGIN/ROLE_CHANGE/CONTENT_TAKEDOWN/MODEL_SWITCH/DEVICE_CMD',
  `resource` VARCHAR(64) NOT NULL COMMENT '操作资源域',
  `resource_id` VARCHAR(64) DEFAULT NULL COMMENT '目标实体ID',
  `detail_json` JSON DEFAULT NULL COMMENT '变更前后参数快照',
  `ip_address` VARCHAR(64) DEFAULT NULL,
  `user_agent` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_audit_user_action` (`user_id`, `action`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管理员与敏感操作审计表';

-- 61. 每日运营大盘汇总报表（Dashboard 极速秒级聚合）
CREATE TABLE IF NOT EXISTS `operation_stat_daily` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `stat_date` DATE NOT NULL COMMENT '统计日期',
  `dau` INT NOT NULL DEFAULT 0 COMMENT '日活跃用户数',
  `mau` INT NOT NULL DEFAULT 0 COMMENT '月活跃用户数',
  `new_users` INT NOT NULL DEFAULT 0 COMMENT '新增注册用户',
  `course_learn_count` INT NOT NULL DEFAULT 0 COMMENT '今日课程学习人次',
  `ai_generate_count` INT NOT NULL DEFAULT 0 COMMENT '今日AI工坊生成次数',
  `community_post_count` INT NOT NULL DEFAULT 0 COMMENT '今日发布作品数',
  `order_count` INT NOT NULL DEFAULT 0 COMMENT '今日商城成交笔数',
  `order_gmv_cents` INT NOT NULL DEFAULT 0 COMMENT '今日成交GMV(分)',
  `fund_added_cents` INT NOT NULL DEFAULT 0 COMMENT '今日注入美育基金(分)',
  `device_active_count` INT NOT NULL DEFAULT 0 COMMENT '今日活跃在线机器人数量',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_stat_date` (`stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='平台每日运营指标汇总表';
