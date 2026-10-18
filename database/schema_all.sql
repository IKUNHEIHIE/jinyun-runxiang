-- =============================================================================
-- 津韵润乡——天津非遗赋能乡村美育智能应用 全表初始化脚本 (61表规范)
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- V1__init_auth_user.sql
-- 身份与用户数据域：用户、角色、权限、画像、成长能量值与徽章
-- =============================================================================

-- 1. 用户表
CREATE TABLE IF NOT EXISTS `sys_user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '用户主键ID',
  `username` VARCHAR(64) NOT NULL COMMENT '登录名/学号/工号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '加密密码',
  `token_version` INT NOT NULL DEFAULT 0,
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


-- =============================================================================
-- V3__ai_workshop_assets.sql
-- AI工坊与媒资域：大文件对象存储元数据、模型注册表、异步任务引擎、重试审计与任务成果资产
-- =============================================================================

-- 24. 统一对象存储与媒资资产表（前置依赖）
CREATE TABLE IF NOT EXISTS `asset` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '资源全局唯一ID',
  `asset_type` VARCHAR(32) NOT NULL COMMENT 'IMAGE(图片)/VIDEO(视频)/AUDIO(音频)/MESH_3D(3D模型)/PPT(课件)/DOC(文档)',
  `object_key` VARCHAR(500) NOT NULL COMMENT 'MinIO/S3 存储桶内路径Key',
  `bucket` VARCHAR(64) NOT NULL DEFAULT 'jinyun-assets' COMMENT '存储桶名称',
  `file_url` VARCHAR(500) DEFAULT NULL COMMENT '公开或CDN直链',
  `mime_type` VARCHAR(128) NOT NULL COMMENT 'MIME类型: 如 image/webp, video/mp4, model/gltf-binary',
  `size_bytes` BIGINT NOT NULL DEFAULT 0 COMMENT '文件字节大小',
  `sha256` CHAR(64) DEFAULT NULL COMMENT 'SHA256哈希指纹',
  `metadata_json` JSON DEFAULT NULL COMMENT '扩展元数据(宽、高、时长、3D面数、材质贴图信息等)',
  `visibility` VARCHAR(16) NOT NULL DEFAULT 'PUBLIC' COMMENT 'PUBLIC/PRIVATE/TEMP',
  `created_by` BIGINT DEFAULT NULL COMMENT '上传者用户ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_type_created` (`asset_type`, `created_at`),
  KEY `idx_sha256` (`sha256`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多模态媒资对象存储元数据表';

-- 22. AI 模型与 LoRA 版本注册表
CREATE TABLE IF NOT EXISTS `ai_model` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '模型ID',
  `code` VARCHAR(64) NOT NULL COMMENT '模型编码: 如 sd15_shadow_puppet_v1, qwen_lesson_planner',
  `name` VARCHAR(128) NOT NULL COMMENT '模型展示名称',
  `task_type` VARCHAR(32) NOT NULL COMMENT 'SHADOW_PUPPET/BRONZE/BALLAD/LACQUER/EMBROIDERY/MESH_3D/LESSON_PLAN',
  `version` VARCHAR(32) NOT NULL DEFAULT '1.0.0' COMMENT '语义化版本',
  `provider` VARCHAR(64) NOT NULL DEFAULT 'LOCAL_WORKER' COMMENT 'LOCAL_WORKER/DASHSCOPE/OPENAI',
  `weights_path` VARCHAR(500) DEFAULT NULL COMMENT '权重或LoRA在MinIO/本地路径',
  `config_json` JSON DEFAULT NULL COMMENT '默认推理参数(步数、cfg_scale、采样器、分辨率)',
  `prompt_template` TEXT DEFAULT NULL COMMENT '系统级非遗风格引导词模板',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/INACTIVE',
  `is_default` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为该类目默认模型',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_code_version` (`code`, `version`),
  KEY `idx_task_type` (`task_type`, `is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI生成模型与LoRA注册表';

-- 20. AI 异步创作任务主表
CREATE TABLE IF NOT EXISTS `ai_task` (
  `task_id` CHAR(32) NOT NULL COMMENT 'UUID任务标识',
  `user_id` BIGINT NOT NULL COMMENT '提交者用户ID',
  `tool_type` VARCHAR(32) NOT NULL COMMENT 'SHADOW_PUPPET/BRONZE/BALLAD/LACQUER/EMBROIDERY/MESH_3D/LESSON_PLAN',
  `status` VARCHAR(20) NOT NULL DEFAULT 'QUEUED' COMMENT 'PENDING/QUEUED/RUNNING/SUCCESS/FAILED/CANCELLED',
  `progress` TINYINT NOT NULL DEFAULT 0 COMMENT '生成进度百分比 0-100',
  `model_id` BIGINT DEFAULT NULL COMMENT '使用的模型ID',
  `model_version` VARCHAR(64) DEFAULT NULL COMMENT '模型版本快照',
  `input_json` JSON NOT NULL COMMENT '输入参数: 灵感词、参考图asset_id、角色偏好等',
  `result_summary_json` JSON DEFAULT NULL COMMENT '结果简要摘要',
  `error_code` VARCHAR(32) DEFAULT NULL COMMENT '失败错误码',
  `error_message` VARCHAR(500) DEFAULT NULL COMMENT '用户可读的失败原因',
  `trace_id` VARCHAR(64) DEFAULT NULL COMMENT '全局全链路追踪ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`task_id`),
  KEY `idx_user_created` (`user_id`, `created_at`),
  KEY `idx_status_updated` (`status`, `updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI异步生成任务主表';

-- 21. AI 任务推理尝试与重试审计
CREATE TABLE IF NOT EXISTS `ai_task_attempt` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `task_id` CHAR(32) NOT NULL,
  `attempt_no` INT NOT NULL DEFAULT 1 COMMENT '重试序号',
  `worker_id` VARCHAR(64) DEFAULT NULL COMMENT '执行节点标识',
  `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ended_at` DATETIME DEFAULT NULL,
  `duration_ms` INT DEFAULT NULL COMMENT '推理耗时毫秒',
  `error_message` TEXT DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_task_attempt` (`task_id`, `attempt_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI任务尝试审计明细表';

-- 23. AI 任务产出资产关联表
CREATE TABLE IF NOT EXISTS `ai_task_asset` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `task_id` CHAR(32) NOT NULL COMMENT '关联任务ID',
  `asset_id` BIGINT NOT NULL COMMENT '关联资源ID',
  `asset_role` VARCHAR(32) NOT NULL DEFAULT 'OUTPUT' COMMENT 'INPUT_SKETCH/OUTPUT_LINE/OUTPUT_COLORED/OUTPUT_3D/OUTPUT_AUDIO',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_task_asset` (`task_id`, `asset_role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI生成资产绑定表';


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
  `is_co_creation` BOOLEAN NOT NULL DEFAULT FALSE,
  `co_creator_name` VARCHAR(64) NULL,
  `co_creator_school` VARCHAR(128) NULL,
  `rural_author_name` VARCHAR(64) NULL,
  `rural_school` VARCHAR(128) NULL,
  `rural_original_url` VARCHAR(500) NULL,
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


-- =============================================================================
-- V5__teacher_classroom.sql
-- 教师教学与班级学情数据域：教师档案、班级、成员绑定、作业、学生作品提交、AI辅助批改与学情统计
-- =============================================================================

-- 33. 教师专属扩展档案
CREATE TABLE IF NOT EXISTS `teacher_profile` (
  `user_id` BIGINT NOT NULL COMMENT '对应sys_user ID',
  `school_name` VARCHAR(128) NOT NULL COMMENT '任教乡村学校',
  `subject` VARCHAR(64) NOT NULL DEFAULT '美术/非遗' COMMENT '学科方向',
  `title` VARCHAR(64) DEFAULT NULL COMMENT '职称',
  `verified_status` VARCHAR(16) NOT NULL DEFAULT 'VERIFIED' COMMENT 'PENDING/VERIFIED/REJECTED',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师专属档案表';

-- 34. 班级信息表
CREATE TABLE IF NOT EXISTS `teacher_class` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '班级ID',
  `teacher_id` BIGINT NOT NULL COMMENT '班主任/授课教师ID',
  `name` VARCHAR(64) NOT NULL COMMENT '班级名称: 如 2026级非遗美育特色一班',
  `grade` VARCHAR(32) NOT NULL COMMENT '年级: 三年级/四年级/初一',
  `school_id` VARCHAR(64) DEFAULT NULL COMMENT '学校代码',
  `invite_code` VARCHAR(16) DEFAULT NULL COMMENT '学生自主加入班级邀请码',
  `student_count` INT NOT NULL DEFAULT 0 COMMENT '当前学生人数',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/ARCHIVED',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_teacher_status` (`teacher_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教师所属教学班级表';

-- 35. 班级学生成员关系表
CREATE TABLE IF NOT EXISTS `class_member` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `class_id` BIGINT NOT NULL,
  `student_id` BIGINT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/QUIT',
  `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_class_student` (`class_id`, `student_id`),
  KEY `idx_student_class` (`student_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级成员关联表';

-- 36. 教师布置作业表
CREATE TABLE IF NOT EXISTS `assignment` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '作业ID',
  `class_id` BIGINT NOT NULL COMMENT '所属班级',
  `teacher_id` BIGINT NOT NULL COMMENT '发布教师',
  `course_id` BIGINT DEFAULT NULL COMMENT '关联课程(可选)',
  `title` VARCHAR(128) NOT NULL COMMENT '作业标题: 如 创作天津皮影角色-穆桂英',
  `type` VARCHAR(32) NOT NULL DEFAULT 'AI_CREATION' COMMENT 'AI_CREATION(线上AI生成)/OFFLINE_HANDMADE(线下非遗实物打卡)',
  `tool_type` VARCHAR(32) DEFAULT NULL COMMENT '限定AI工坊工具类型',
  `deadline` DATETIME NOT NULL COMMENT '截止提交时间',
  `description` TEXT NOT NULL COMMENT '作业具体要求与文化要点',
  `rubric_json` JSON DEFAULT NULL COMMENT '评价维度与权重打分标准',
  `lesson_plan_id` BIGINT DEFAULT NULL COMMENT '关联的AI智能备课教案ID',
  `status` VARCHAR(16) NOT NULL DEFAULT 'PUBLISHED' COMMENT 'DRAFT/PUBLISHED/CLOSED',
  `contest_id` BIGINT DEFAULT NULL COMMENT '所属对抗赛ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_class_deadline` (`class_id`, `deadline`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='教学作业发布表';

-- 37. 学生作业提交记录表
CREATE TABLE IF NOT EXISTS `assignment_submission` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '提交ID',
  `assignment_id` BIGINT NOT NULL,
  `student_id` BIGINT NOT NULL,
  `content` TEXT DEFAULT NULL COMMENT '学生创作心得体会',
  `asset_id` BIGINT DEFAULT NULL COMMENT '提交的作品图片/音频/3D资源ID',
  `source_task_id` CHAR(32) DEFAULT NULL COMMENT '关联AI生成任务ID',
  `status` VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED' COMMENT 'SUBMITTED/REVIEWED/RETURNED',
  `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_assign_student` (`assignment_id`, `student_id`),
  KEY `idx_student_assign` (`student_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生作业提交表';

-- 38. 作业评价与AI辅助初审表
CREATE TABLE IF NOT EXISTS `assignment_review` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `submission_id` BIGINT NOT NULL COMMENT '关联作业提交ID',
  `teacher_id` BIGINT DEFAULT NULL COMMENT '批改教师ID',
  `score` INT NOT NULL DEFAULT 90 COMMENT '最终得分(0-100)',
  `comment` TEXT DEFAULT NULL COMMENT '教师综合评语',
  `ai_suggestion_json` JSON DEFAULT NULL COMMENT 'AI多模态大模型初审推荐评语与评分',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_submission_review` (`submission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='作业批阅与AI辅助评语表';

-- 班级对抗赛
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

-- 班级学情日常汇总表（避免高频全量聚合扫描）
CREATE TABLE IF NOT EXISTS `class_daily_stats` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `class_id` BIGINT NOT NULL,
  `stat_date` DATE NOT NULL,
  `course_completion_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '课程完成率百分比',
  `quiz_avg_score` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '随堂测验平均分',
  `assignment_submit_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '作业按时提交率',
  `avg_energy_value` INT NOT NULL DEFAULT 0 COMMENT '人均非遗能量值',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_class_date` (`class_id`, `stat_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='班级学情日统计表';


-- =============================================================================
-- V6__activity_mall.sql
-- 文旅活动打卡与电商助农数据域：非遗地图地标、线下/直播活动、预约签到、文创与农特产商城、订单与美育基金
-- =============================================================================

-- 39. 非遗美育地标点
CREATE TABLE IF NOT EXISTS `heritage_landmark` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '地标ID',
  `name` VARCHAR(128) NOT NULL COMMENT '地标名称: 如 杨柳青古镇年画馆/泥人张美术馆/独乐寺',
  `category` VARCHAR(64) NOT NULL COMMENT '非遗类型: 民间美术/传统技艺/传统戏剧/曲艺',
  `address` VARCHAR(255) NOT NULL COMMENT '详细地址',
  `district` VARCHAR(64) NOT NULL COMMENT '所属区县: 西青区/南开区/蓟州区等',
  `latitude` DECIMAL(10,6) NOT NULL COMMENT '纬度',
  `longitude` DECIMAL(10,6) NOT NULL COMMENT '经度',
  `geofence_radius_meters` INT NOT NULL DEFAULT 500 COMMENT '打卡电子围栏有效半径(米)',
  `description` TEXT DEFAULT NULL COMMENT '历史沿革与非遗故事',
  `cover_url` VARCHAR(500) DEFAULT NULL COMMENT '地标展示大图',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE' COMMENT 'ACTIVE/INACTIVE',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_district_cat` (`district`, `category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='非遗地标地理信息表';

-- 40. 非遗活动主表
CREATE TABLE IF NOT EXISTS `activity` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '活动ID',
  `title` VARCHAR(128) NOT NULL COMMENT '活动名称: 如 天津皮影老艺人线下双师教学营',
  `type` VARCHAR(32) NOT NULL DEFAULT 'OFFLINE' COMMENT 'OFFLINE(线下实地)/LIVE(双师线上直播)/CHALLENGE(线上打卡)',
  `landmark_id` BIGINT DEFAULT NULL COMMENT '关联地标ID',
  `master_name` VARCHAR(64) DEFAULT NULL COMMENT '特邀非遗传承人姓名',
  `start_at` DATETIME NOT NULL COMMENT '开始时间',
  `end_at` DATETIME NOT NULL COMMENT '结束时间',
  `capacity` INT NOT NULL DEFAULT 100 COMMENT '预约名额上限',
  `reserved_count` INT NOT NULL DEFAULT 0 COMMENT '已预约人次',
  `badge_id` BIGINT DEFAULT NULL COMMENT '打卡/参与后解锁的限定徽章ID',
  `energy_reward` INT NOT NULL DEFAULT 30 COMMENT '参与奖励能量值',
  `status` VARCHAR(16) NOT NULL DEFAULT 'PUBLISHED' COMMENT 'DRAFT/PUBLISHED/ONGOING/ENDED/CANCELLED',
  `description` TEXT NOT NULL COMMENT '活动详情说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_activity_time` (`start_at`, `end_at`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='非遗活动与预约表';

-- 41. 活动名额预约记录表
CREATE TABLE IF NOT EXISTS `activity_reservation` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `activity_id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'CONFIRMED' COMMENT 'CONFIRMED/CANCELLED/ATTENDED',
  `reserved_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_act_user_reserve` (`activity_id`, `user_id`),
  KEY `idx_user_reserve` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='活动名额预约表';

-- 42. 线下实地打卡签到表
CREATE TABLE IF NOT EXISTS `activity_checkin` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `activity_id` BIGINT DEFAULT NULL COMMENT '关联活动ID(可为空, 表示纯地标打卡)',
  `landmark_id` BIGINT NOT NULL COMMENT '打卡地标ID',
  `user_id` BIGINT NOT NULL,
  `latitude` DECIMAL(10,6) NOT NULL COMMENT '签到时经纬度',
  `longitude` DECIMAL(10,6) NOT NULL,
  `distance_meters` INT NOT NULL COMMENT '距离地标中心误差距离(米)',
  `location_accuracy_meters` DECIMAL(10,2) DEFAULT NULL,
  `geofence_status` VARCHAR(16) DEFAULT NULL,
  `checked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_landmark` (`user_id`, `landmark_id`),
  KEY `idx_user_checkin` (`user_id`, `checked_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='非遗地标打卡签到记录表';

-- 43. 文创与乡村农特产商品表
CREATE TABLE IF NOT EXISTS `product` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '商品ID',
  `name` VARCHAR(128) NOT NULL COMMENT '商品名称: 如 杨柳青木版年画DIY套装/蓟州盘山磨盘柿',
  `category` VARCHAR(32) NOT NULL DEFAULT 'CULTURAL_CREATIVE' COMMENT 'CULTURAL_CREATIVE(非遗文创)/AGRI_PRODUCT(助农特色农产)',
  `cover_url` VARCHAR(500) NOT NULL COMMENT '封面主图',
  `origin_place` VARCHAR(128) DEFAULT NULL COMMENT '产地乡村: 如 西青区杨柳青镇/蓟州区官庄镇',
  `story` TEXT DEFAULT NULL COMMENT '非遗背后的乡村振兴故事',
  `fund_rate_percent` DECIMAL(5,2) NOT NULL DEFAULT 10.00 COMMENT '每单注入乡村美育基金比例(如 10%)',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ON_SALE' COMMENT 'ON_SALE/OFF_SALE',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_product_cat_status` (`category`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文创与农特产商品主表';

-- 44. 商品SKU库存与价格表
CREATE TABLE IF NOT EXISTS `product_sku` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `product_id` BIGINT NOT NULL,
  `sku_code` VARCHAR(64) NOT NULL COMMENT 'SKU规格条码',
  `name` VARCHAR(128) NOT NULL COMMENT '规格名称: 如 标准手工礼盒装/5斤家庭装',
  `price_cents` INT NOT NULL DEFAULT 0 COMMENT '单价(分)',
  `stock` INT NOT NULL DEFAULT 100 COMMENT '剩余库存',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_sku_code` (`sku_code`),
  KEY `idx_product_sku` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='商品SKU规格与库存表';

-- 45. 助农商城订单主表
CREATE TABLE IF NOT EXISTS `order_main` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `order_no` VARCHAR(64) NOT NULL COMMENT '唯一订单流水号',
  `client_request_id` VARCHAR(64) DEFAULT NULL,
  `user_id` BIGINT NOT NULL COMMENT '下单用户ID',
  `total_amount_cents` INT NOT NULL DEFAULT 0 COMMENT '实付总额(分)',
  `fund_amount_cents` INT NOT NULL DEFAULT 0 COMMENT '贡献至美育基金金额(分)',
  `status` VARCHAR(24) NOT NULL DEFAULT 'CREATED' COMMENT 'CREATED/PENDING_PAYMENT/PAID/FULFILLING/COMPLETED/CANCELLED/REFUNDED',
  `receiver_name` VARCHAR(64) DEFAULT NULL,
  `receiver_phone` VARCHAR(32) DEFAULT NULL,
  `receiver_address` VARCHAR(255) DEFAULT NULL,
  `pay_time` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  UNIQUE KEY `uk_order_client_request_id` (`client_request_id`),
  KEY `idx_user_order` (`user_id`, `created_at`),
  KEY `idx_order_status` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='助农文创订单主表';

-- 46. 订单明细项快照
CREATE TABLE IF NOT EXISTS `order_item` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `product_id` BIGINT NOT NULL,
  `sku_id` BIGINT NOT NULL,
  `product_name` VARCHAR(128) NOT NULL,
  `sku_name` VARCHAR(128) NOT NULL,
  `price_cents` INT NOT NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order_item` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单明细快照表';

-- 47. 支付交易流水表
CREATE TABLE IF NOT EXISTS `payment_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `payment_no` VARCHAR(64) NOT NULL COMMENT '支付流水号',
  `channel` VARCHAR(32) NOT NULL DEFAULT 'WECHAT' COMMENT 'WECHAT/ALIPAY/MOCK_PAY',
  `amount_cents` INT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'SUCCESS' COMMENT 'PENDING/SUCCESS/FAILED',
  `paid_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_payment_no` (`payment_no`),
  KEY `idx_order_pay` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付流水记录表';

-- 48. 助农收益分账明细
CREATE TABLE IF NOT EXISTS `settlement_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `party_type` VARCHAR(32) NOT NULL COMMENT 'FARMER(农户)/HERITAGE_ARTISAN(非遗工坊)/PLATFORM(运营成本)',
  `party_id` BIGINT DEFAULT NULL,
  `amount_cents` INT NOT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'SETTLED' COMMENT 'PENDING/SETTLED',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order_settle` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='助农收益拆分结算表';

-- 49. 乡村非遗美育基金资金台账
CREATE TABLE IF NOT EXISTS `fund_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `source_order_id` BIGINT NOT NULL COMMENT '来源订单ID',
  `amount_cents` INT NOT NULL COMMENT '汇入基金金额(分)',
  `purpose` VARCHAR(128) NOT NULL DEFAULT '乡村小学非遗美育耗材捐赠' COMMENT '基金用途定向',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ALLOCATED' COMMENT 'ALLOCATED(已留存)/EXPENDED(已支出使用)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_source_order` (`source_order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='乡村非遗美育专项基金表';


-- =============================================================================
-- V7__device_gateway.sql
-- 具身智能与物联网设备接入数据域：设备台账、能力声明、遥测数据、控制命令流与事件上报
-- =============================================================================

-- 50. 具身智能与多模态设备主表
CREATE TABLE IF NOT EXISTS `device` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '设备自增ID',
  `device_code` VARCHAR(64) NOT NULL COMMENT '设备唯一物理编号/MAC地址/UUID',
  `device_name` VARCHAR(128) NOT NULL COMMENT '设备名称: 如 天津皮影表演机器人-01号',
  `model` VARCHAR(64) NOT NULL DEFAULT 'ROBOT_SHADOW_V1' COMMENT '硬件型号',
  `firmware_version` VARCHAR(32) NOT NULL DEFAULT '1.0.0' COMMENT '固件版本',
  `school_id` VARCHAR(64) DEFAULT NULL COMMENT '部署所属乡村学校',
  `ip_address` VARCHAR(64) DEFAULT NULL COMMENT '最近上线IP',
  `status` VARCHAR(16) NOT NULL DEFAULT 'OFFLINE' COMMENT 'ONLINE/OFFLINE/BUSY/ERROR',
  `last_seen_at` DATETIME DEFAULT NULL COMMENT '最后心跳活跃时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_device_code` (`device_code`),
  KEY `idx_device_status` (`status`, `last_seen_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='具身智能设备台账表';

-- 51. 设备能力声明表
CREATE TABLE IF NOT EXISTS `device_capability` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `device_id` BIGINT NOT NULL,
  `capability_code` VARCHAR(64) NOT NULL COMMENT 'CAMERA_VISION(视觉识别)/SERVO_ACTUATION(伺服舵机肢体动作)/SPEECH_TTS(语音播报)/SPEECH_ASR(语音拾音)',
  `config_json` JSON DEFAULT NULL COMMENT '能力参数与接口规范',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_device_cap` (`device_id`, `capability_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备外设能力表';

-- 52. 设备运行遥测监控表
CREATE TABLE IF NOT EXISTS `device_telemetry` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `device_id` BIGINT NOT NULL,
  `metric_code` VARCHAR(32) NOT NULL COMMENT 'BATTERY_PCT(电量)/WIFI_RSSI(信号)/CPU_TEMP(温度)/MOTOR_STATUS',
  `metric_value` VARCHAR(64) NOT NULL COMMENT '指标数值',
  `reported_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_dev_telemetry` (`device_id`, `metric_code`, `reported_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备遥测数据表';

-- 53. 设备下发控制命令表
CREATE TABLE IF NOT EXISTS `device_command` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `command_id` VARCHAR(64) NOT NULL COMMENT '命令UUID流水号',
  `device_id` BIGINT NOT NULL,
  `command_type` VARCHAR(64) NOT NULL COMMENT 'PERFORM_SHADOW_PLAY(皮影表演动作)/SPEAK_EXPLANATION(非遗讲解语音)/RESET',
  `payload_json` JSON NOT NULL COMMENT '命令指令参数(动作序列轴角/文本语音内容)',
  `status` VARCHAR(16) NOT NULL DEFAULT 'SENT' COMMENT 'SENT/ACKED/EXECUTED/FAILED/TIMEOUT',
  `sent_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `ack_at` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_command_id` (`command_id`),
  KEY `idx_device_cmd` (`device_id`, `status`, `sent_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备控制指令表';

-- 54. 设备主动上报事件表
CREATE TABLE IF NOT EXISTS `device_event` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `event_id` VARCHAR(64) NOT NULL COMMENT '事件UUID',
  `device_id` BIGINT NOT NULL,
  `event_type` VARCHAR(64) NOT NULL COMMENT 'STUDENT_WORK_DETECTED(摄像头识别到学生手工作品)/VOICE_QUERY/LOW_BATTERY',
  `payload_json` JSON NOT NULL COMMENT '事件详情(拍照图片临时URL/识别结果/唤醒词)',
  `occurred_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dev_event_id` (`event_id`),
  KEY `idx_device_event` (`device_id`, `occurred_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备上报事件记录表';


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


SET FOREIGN_KEY_CHECKS = 1;



-- Additional application tables (also available in V9).
CREATE TABLE IF NOT EXISTS sys_config (
	id INTEGER NOT NULL AUTO_INCREMENT,
	config_key VARCHAR(64) NOT NULL,
	config_value TEXT NOT NULL,
	description VARCHAR(255),
	updated_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE (config_key)
);

CREATE TABLE IF NOT EXISTS folk_festival (
	id BIGINT NOT NULL AUTO_INCREMENT,
	title VARCHAR(128) NOT NULL,
	solar_date VARCHAR(32),
	lunar_date VARCHAR(32) NOT NULL,
	category VARCHAR(64),
	tag VARCHAR(64),
	customs VARCHAR(255),
	description TEXT,
	cover_url VARCHAR(500),
	status VARCHAR(16),
	sort_order INTEGER,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS philanthropy_supply (
	id BIGINT NOT NULL AUTO_INCREMENT,
	school_name VARCHAR(128) NOT NULL,
	district VARCHAR(64) NOT NULL,
	materials_name VARCHAR(128) NOT NULL,
	quantity INTEGER NOT NULL,
	unit VARCHAR(16),
	beneficiary_students INTEGER,
	delivered_date VARCHAR(32),
	batch_no VARCHAR(64),
	photo_url VARCHAR(500),
	status VARCHAR(16),
	created_at DATETIME,
	PRIMARY KEY (id)
);

-- Additive migration for the MasterGo Android client. MySQL 8.0.
-- Apply after V9. Existing business data and tables are preserved.
CREATE TABLE IF NOT EXISTS heritage_entry (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(128) NOT NULL,
  category VARCHAR(64) NOT NULL,
  era VARCHAR(128),
  summary VARCHAR(1000),
  cover_url VARCHAR(500),
  model_url VARCHAR(500),
  content_json JSON NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'PUBLISHED',
  created_at DATETIME,
  updated_at DATETIME,
  INDEX ix_heritage_entry_category (category)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS user_collection (
  user_id BIGINT NOT NULL,
  target_type VARCHAR(16) NOT NULL,
  target_id BIGINT NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (user_id, target_type, target_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS user_follow (
  follower_id BIGINT NOT NULL,
  followed_id BIGINT NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (follower_id, followed_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS course_rating (
  user_id BIGINT NOT NULL,
  course_id BIGINT NOT NULL,
  score INT NOT NULL,
  comment VARCHAR(1000) NOT NULL DEFAULT '',
  updated_at DATETIME,
  PRIMARY KEY (user_id, course_id), CONSTRAINT ck_course_rating_score CHECK (score BETWEEN 1 AND 5)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS user_feedback (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  content TEXT NOT NULL,
  contact VARCHAR(128),
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
  created_at DATETIME,
  reply_text TEXT,
  handled_by BIGINT,
  handled_at DATETIME,
  INDEX ix_user_feedback_user_id (user_id)
) CHARACTER SET utf8mb4;


-- V11: additive teacher collaboration tables. Apply after V10.
CREATE TABLE IF NOT EXISTS lesson_plan_record (
	id BIGINT NOT NULL AUTO_INCREMENT,
	teacher_id BIGINT NOT NULL,
	title VARCHAR(255) NOT NULL,
	grade VARCHAR(64) NOT NULL,
	topic VARCHAR(128) NOT NULL,
	duration_minutes INTEGER NOT NULL,
	content_json JSON NOT NULL,
	source VARCHAR(128) NOT NULL,
	request_id VARCHAR(64),
	request_mode VARCHAR(16),
	created_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_lesson_plan_record_teacher_id (teacher_id),
	CONSTRAINT uk_lesson_plan_request UNIQUE (teacher_id, request_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_notice (
	id BIGINT NOT NULL AUTO_INCREMENT,
	class_id BIGINT NOT NULL,
	teacher_id BIGINT NOT NULL,
	title VARCHAR(128) NOT NULL,
	content TEXT NOT NULL,
	created_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_class_notice_class_id (class_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_attendance (
	class_id BIGINT NOT NULL,
	student_id BIGINT NOT NULL,
	day VARCHAR(10) NOT NULL,
	status VARCHAR(16) NOT NULL,
	recorded_by BIGINT NOT NULL,
	updated_at DATETIME,
	PRIMARY KEY (class_id, student_id, day)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_session (
	id BIGINT NOT NULL AUTO_INCREMENT,
	class_id BIGINT NOT NULL,
	host_id BIGINT NOT NULL,
	title VARCHAR(128) NOT NULL,
	stream_url VARCHAR(500),
	status VARCHAR(16) NOT NULL,
	created_at DATETIME,
	ended_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_class_session_class_id (class_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_message (
	id BIGINT NOT NULL AUTO_INCREMENT,
	session_id BIGINT NOT NULL,
	user_id BIGINT NOT NULL,
	type VARCHAR(16) NOT NULL,
	content VARCHAR(1000) NOT NULL,
	created_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_class_message_session_id (session_id)
) CHARACTER SET utf8mb4;


CREATE TABLE IF NOT EXISTS exchange_item (
  id BIGINT NOT NULL AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  cover_url VARCHAR(500),
  energy_cost INT NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS energy_exchange (
  id BIGINT NOT NULL AUTO_INCREMENT,
  request_id VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  item_id BIGINT NOT NULL,
  item_name VARCHAR(128) NOT NULL,
  energy_cost INT NOT NULL,
  receiver_name VARCHAR(64) NOT NULL,
  receiver_phone VARCHAR(32) NOT NULL,
  receiver_address VARCHAR(255) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'REQUESTED',
  tracking_no VARCHAR(128),
  created_at DATETIME,
  handling_note VARCHAR(500) NOT NULL DEFAULT '',
  handled_by BIGINT,
  handled_at DATETIME,
  PRIMARY KEY (id),
  UNIQUE KEY uk_exchange_request (request_id),
  KEY ix_energy_exchange_user_id (user_id)
);


CREATE TABLE IF NOT EXISTS walk_session (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  active_seconds INT NOT NULL DEFAULT 0,
  distance_meters INT NOT NULL DEFAULT 0,
  status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  last_latitude NUMERIC(10,6),
  last_longitude NUMERIC(10,6),
  last_point_at DATETIME,
  started_at DATETIME,
  ended_at DATETIME,
  PRIMARY KEY (id),
  KEY ix_walk_session_user_id (user_id)
);

-- V14: artwork gallery/metadata and comment likes.
CREATE TABLE IF NOT EXISTS community_post_detail (
  post_id BIGINT NOT NULL,
  gallery_json JSON NOT NULL,
  specifications_json JSON NOT NULL,
  appreciation_json JSON NOT NULL,
  PRIMARY KEY (post_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS community_comment_like (
  comment_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (comment_id, user_id)
) CHARACTER SET utf8mb4;

-- V15: one learning record per user and Shanghai calendar day.
CREATE TABLE IF NOT EXISTS learning_day (
  user_id BIGINT NOT NULL,
  day DATE NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (user_id, day)
) CHARACTER SET utf8mb4;
