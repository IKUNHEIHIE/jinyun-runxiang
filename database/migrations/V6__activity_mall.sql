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
  `checked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_landmark_date` (`user_id`, `landmark_id`),
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
