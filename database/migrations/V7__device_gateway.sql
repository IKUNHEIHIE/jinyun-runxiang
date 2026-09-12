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
