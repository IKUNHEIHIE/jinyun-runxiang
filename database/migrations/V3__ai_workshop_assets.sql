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
