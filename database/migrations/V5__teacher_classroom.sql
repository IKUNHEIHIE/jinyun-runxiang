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
