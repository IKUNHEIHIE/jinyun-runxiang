-- =============================================================================
-- seed_data.sql
-- 《津韵润乡》天津非遗赋能乡村美育智能应用 - 初始种子数据
-- 覆盖：用户、角色、课程、测验、AI模型、社区帖子、教师班级、地标、助农商品、设备台账、运营统计
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 角色初始化
INSERT INTO `sys_role` (`id`, `code`, `name`, `description`, `status`) VALUES
(1, 'ADMIN', '运营管理员', '全平台内容、模型、审核与运营权限', 'ACTIVE'),
(2, 'TEACHER', '乡村教师', '备课、作业布置、学情看板、双师课堂', 'ACTIVE'),
(3, 'STUDENT', '乡村学生', '课程学习、AI工坊创作、社区互动、打卡', 'ACTIVE'),
(4, 'TOURIST', '社会游客', '非遗文化浏览与文创助农支持', 'ACTIVE')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 2. 初始账号 (密码哈希均对应明文+salt的SHA256或bcrypt，开发测试内置默认密码：admin123, teacher123, student123)
-- SHA256 of 'admin123': 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa82280f1a82e3eb0
-- SHA256 of 'teacher123': ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f
-- SHA256 of 'student123': 60e9094fe5b706c9b466faaa0ba9db3f5da1e4a778e8fbab12a326ff73634027
INSERT INTO `sys_user` (`id`, `username`, `password_hash`, `nickname`, `avatar_url`, `role_code`, `grade`, `status`, `phone`) VALUES
(1, 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa82280f1a82e3eb0', '津韵总管', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150', 'ADMIN', '成人', 'ACTIVE', '13800000001'),
(2, 'teacher_wang', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', '王秀兰老师', 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150', 'TEACHER', '教师', 'ACTIVE', '13800000002'),
(3, 'student_ming', '60e9094fe5b706c9b466faaa0ba9db3f5da1e4a778e8fbab12a326ff73634027', '李小明', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 'STUDENT', '小学三年级', 'ACTIVE', '13800000003'),
(4, 'student_hua', '60e9094fe5b706c9b466faaa0ba9db3f5da1e4a778e8fbab12a326ff73634027', '张小华', 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=150', 'STUDENT', '小学四年级', 'ACTIVE', '13800000004'),
(5, 'tourist_tianjin', '60e9094fe5b706c9b466faaa0ba9db3f5da1e4a778e8fbab12a326ff73634027', '津门漫步客', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150', 'TOURIST', '游客', 'ACTIVE', '13800000005')
ON DUPLICATE KEY UPDATE `nickname`=VALUES(`nickname`);

-- 3. 用户画像与教师档案
INSERT INTO `user_profile` (`user_id`, `school_name`, `district`, `bio`, `avatar_config_json`) VALUES
(2, '蓟州区下营镇中心小学', '蓟州区', '让每一个乡村孩子感受家乡非遗的美', '{"outfit":"TEACHER_HANFU","accessory":"BRUSH"}'),
(3, '蓟州区下营镇中心小学', '蓟州区', '我是津韵润乡非遗小匠人！', '{"outfit":"SHADOW_APPRENTICE","hat":"TIGER_CAP"}'),
(4, '宝坻区大口屯镇初级中学', '宝坻区', '热爱泥人张与天津评剧', '{"outfit":"MODERN_FOLK","accessory":"FAN"}')
ON DUPLICATE KEY UPDATE `school_name`=VALUES(`school_name`);

INSERT INTO `teacher_profile` (`user_id`, `school_name`, `subject`, `title`, `verified_status`) VALUES
(2, '蓟州区下营镇中心小学', '美术/乡村美育', '一级教师', 'VERIFIED')
ON DUPLICATE KEY UPDATE `subject`=VALUES(`subject`);

-- 4. 学生成长能量值与等级
INSERT INTO `user_growth` (`user_id`, `energy_value`, `level_code`) VALUES
(3, 1280, 'LV3_CRAFTSMAN'),
(4, 640, 'LV2_JOURNEYMAN')
ON DUPLICATE KEY UPDATE `energy_value`=VALUES(`energy_value`);

-- 5. 徽章规则定义
INSERT INTO `badge` (`id`, `code`, `name`, `description`, `icon_url`, `condition_json`) VALUES
(1, 'BADGE_FIRST_COURSE', '非遗初探者', '完成第一节天津非遗微课堂学习', 'https://img.icons8.com/color/96/scroll.png', '{"type":"COURSE_COUNT","target":1}'),
(2, 'BADGE_SHADOW_MASTER', '津门皮影小匠人', '在AI工坊成功设计并生成1部皮影角色', 'https://img.icons8.com/color/96/puppet.png', '{"type":"AI_TOOL","tool":"SHADOW_PUPPET"}'),
(3, 'BADGE_BRONZE_ARTISAN', '金石青铜巧手', '完成青铜纹样复原与氧化渲染制作', 'https://img.icons8.com/color/96/antique.png', '{"type":"AI_TOOL","tool":"BRONZE"}'),
(4, 'BADGE_HERITAGE_PIONEER', '乡村美育使者', '在线下非遗地标成功签到打卡', 'https://img.icons8.com/color/96/marker.png', '{"type":"CHECKIN_COUNT","target":1}')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

INSERT INTO `user_badge` (`user_id`, `badge_id`, `unlocked_at`) VALUES
(3, 1, '2026-09-01 10:00:00'),
(3, 2, '2026-09-05 14:30:00')
ON DUPLICATE KEY UPDATE `unlocked_at`=VALUES(`unlocked_at`);

-- 6. 核心非遗课程与章节
INSERT INTO `course` (`id`, `title`, `subtitle`, `category`, `age_group`, `cover_url`, `description`, `duration_minutes`, `energy_reward`, `view_count`, `status`) VALUES
(1, '津门皮影戏：光影里的民间传奇', '学习皮影生旦净丑造型与操纵古法', 'SHADOW_PUPPET', 'PRIMARY_LOW', 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600', '皮影戏又称“影子戏”，天津皮影戏造型生动、刻工精细。本课带小朋友们了解皮影由驴皮制成的精湛工艺，探索光影交错间的人物神态，并在AI工坊动手创作属于自己的皮影角色。', 45, 60, 1850, 'PUBLISHED'),
(2, '杨柳青木版年画：点染岁时吉祥', '木版套印与半印半画的传统年味', 'PAINTING', 'PRIMARY_LOW', 'https://images.unsplash.com/photo-1582560475093-ba66accbc424?w=600', '杨柳青年画产生于明代崇祯年间，以“勾、刻、印、绘、裱”五大工序闻名，尤其是“抱鱼娃娃”等经典画样，寓意连年有余。', 50, 60, 2340, 'PUBLISHED'),
(3, '泥人张彩塑艺术：捏出指尖百态', '随手捏就神形兼备的民间雕塑', 'CLAY', 'PRIMARY_HIGH', 'https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=600', '自清代道光年间张明山开创以来，泥人张彩塑历经六代相传，用细腻河泥捏塑出生动人物，施以矿物颜料，久放不裂。', 40, 50, 1420, 'PUBLISHED'),
(4, '津门鼓曲与三弦：韵白流转唱津城', '领略骆派京韵大鼓的吐字行腔', 'BALLAD', 'JUNIOR', 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600', '京韵大鼓发源于清末民初，以三弦、四胡伴奏，演员自击鼓板。课上带你品味骆玉笙大师经典《重整河山待后生》的刚劲豪迈。', 35, 50, 980, 'PUBLISHED'),
(5, '青铜饕餮神兽：纹样里的古老密码', '重现商周汉代青铜礼乐的神秘图腾', 'BRONZE', 'PRIMARY_HIGH', 'https://images.unsplash.com/photo-1569783727725-b88d3e230756?w=600', '探索天津博物馆珍藏青铜器上的饕餮纹、夔龙纹，理解青铜铸造、范铸法工艺，并通过AI创作属于自己的非遗青铜守护兽。', 45, 60, 1620, 'PUBLISHED'),
(6, '古法大漆与螺钿：天然髹饰之道', '用一髹一缀装点器物的温润光华', 'LACQUER', 'JUNIOR', 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600', '从天然漆树采割生漆，结合贝壳鲍鱼贝切片打磨入漆，形成光彩变幻的非遗螺钿漆器，感受古人巧夺天工的匠心。', 60, 80, 890, 'PUBLISHED')
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

INSERT INTO `course_chapter` (`id`, `course_id`, `seq`, `title`, `video_url`, `duration_seconds`, `key_points_json`) VALUES
(1, 1, 1, '第一讲：白布映光芒——认识皮影家族', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4', 620, '["皮影的材质选用驴皮与牛皮","生旦净丑四大行当脸谱特点","操纵杆三根签的力学原理"]'),
(2, 1, 2, '第二讲：操杆舞影——动起来的孙悟空', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4', 780, '["关节铆接技巧","台步走法与翻跟头","光影距离与放大缩小效应"]'),
(3, 1, 3, '第三讲：AI工坊实操——设计新时代皮影', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4', 540, '["AI提示词角色描述","线稿轮廓提取与激光打印","组装自己的小皮影"]'),
(4, 2, 1, '第一讲：年画娃娃抱鲤鱼——杨柳青的吉祥画', 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4', 680, '["杜梨木版雕刻技巧","矿物颜料调配","红黄绿青紫传统配色法则"]')
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

-- 7. 随堂测验与题目
INSERT INTO `quiz` (`id`, `course_id`, `chapter_id`, `title`, `pass_score`, `energy_reward`) VALUES
(1, 1, 1, '津门皮影戏基础知识小测验', 60, 20)
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

INSERT INTO `quiz_question` (`id`, `quiz_id`, `seq`, `type`, `content`, `options_json`, `answer_json`, `explanation`, `score`) VALUES
(1, 1, 1, 'SINGLE', '传统天津皮影人偶主要使用哪种材料雕刻制成？', '[{"key":"A","text":"塑料片"},{"key":"B","text":"驴皮或牛皮"},{"key":"C","text":"普通卡纸"},{"key":"D","text":"布料"}]', '["B"]', '传统皮影选取质地坚韧通透的驴皮或牛皮，经浸泡、刮薄、打磨后精细雕镂。', 30),
(2, 1, 2, 'SINGLE', '皮影表演者主要通过几根控制杆来操纵皮影人偶？', '[{"key":"A","text":"1根"},{"key":"B","text":"2根"},{"key":"C","text":"3根"},{"key":"D","text":"5根"}]', '["C"]', '皮影通常有一根主杆连接颈部，两根手杆分别连接双手，俗称“三签操纵”。', 35),
(3, 1, 3, 'JUDGE', '在皮影戏中，角色离幕布越远，投影在幕布上的影子越清晰？', '[{"key":"A","text":"正确"},{"key":"B","text":"错误"}]', '["B"]', '皮影人偶必须紧贴幕布才能呈现锐利清晰的剪影，远离幕布时影子会变大且模糊虚化。', 35)
ON DUPLICATE KEY UPDATE `content`=VALUES(`content`);

-- 8. AI 模型注册与配置
INSERT INTO `ai_model` (`id`, `code`, `name`, `task_type`, `version`, `provider`, `config_json`, `prompt_template`, `status`, `is_default`) VALUES
(1, 'lora_tianjin_shadow_v1', '津韵皮影生成模型LoRA', 'SHADOW_PUPPET', '1.0.0', 'LOCAL_WORKER', '{"steps":25,"cfg":7.5,"width":512,"height":768}', 'Tianjin folk shadow puppetry, translucent leather texture, hollow carving patterns, traditional theatrical costume, sharp silhouette, folk art masterpiece', 'ACTIVE', 1),
(2, 'bronze_pattern_pro_v2', '青铜神兽纹样生成引擎', 'BRONZE', '2.0.0', 'LOCAL_WORKER', '{"steps":30,"cfg":8.0,"sampler":"Euler a"}', 'Ancient Chinese bronze vessel pattern, taotie motif, intricate geometric relief, antique patina oxide finish, high resolution, symmetrical ornament', 'ACTIVE', 1),
(3, 'ballad_rhythm_ai_v1', '津派鼓曲节奏与伴奏合成器', 'BALLAD', '1.0.0', 'LOCAL_WORKER', '{"tempo":85,"scale":"pentatonic"}', 'Tianjin Jingyun Dagu rhythm, traditional sanxian and drum beat accompaniment, authentic folk melody', 'ACTIVE', 1),
(4, 'qwen_heritage_rag', '津韵非遗大模型问答与智能备课', 'LESSON_PLAN', '2.5.0', 'DASHSCOPE', '{"temperature":0.7,"max_tokens":2048}', '你是一位拥有30年天津非遗传承与乡村美育教学经验的特级教师。请根据学段与非遗主题，输出具有童趣性、实践性和地域文化深度的高质量教学方案。', 'ACTIVE', 1)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 9. 教师班级与作业
INSERT INTO `teacher_class` (`id`, `teacher_id`, `name`, `grade`, `school_id`, `invite_code`, `student_count`, `status`) VALUES
(1, 2, '蓟州非遗美育三年级一班', '三年级', 'SCH_JIZHOU_01', 'JYRX88', 2, 'ACTIVE')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

INSERT INTO `class_member` (`class_id`, `student_id`, `status`) VALUES
(1, 3, 'ACTIVE'),
(1, 4, 'ACTIVE')
ON DUPLICATE KEY UPDATE `status`=VALUES(`status`);

INSERT INTO `assignment` (`id`, `class_id`, `teacher_id`, `title`, `type`, `tool_type`, `deadline`, `description`, `status`) VALUES
(1, 1, 2, '【创作实践】设计你心目中的现代天津皮影小英雄', 'AI_CREATION', 'SHADOW_PUPPET', '2026-09-30 23:59:59', '请同学们结合在第一课学习的生旦净丑知识，利用AI工坊创作一个身着传统戏服的现代角色皮影，并附上30字以上的角色故事！', 'PUBLISHED')
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

-- 10. 社区话题与示范作品
INSERT INTO `community_topic` (`id`, `name`, `description`, `cover_url`, `post_count`, `status`) VALUES
(1, '#我画津门新皮影', '发挥想象，用AI赋予传统皮影人偶新生命！', 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=500', 42, 'ACTIVE'),
(2, '#寻找身边的非遗印记', '记录津沽大地的老手艺与乡村故事', 'https://images.unsplash.com/photo-1582560475093-ba66accbc424?w=500', 28, 'ACTIVE')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

INSERT INTO `community_post` (`id`, `user_id`, `title`, `content`, `category`, `cover_url`, `topic_id`, `status`, `is_featured`, `heritage_master_like`, `like_count`, `comment_count`, `favorite_count`, `view_count`) VALUES
(1, 3, '我设计的“穆桂英智破天门阵”皮影女将', '在王老师的辅导下，我用AI工坊生成了穆桂英的皮影角色！头戴七星额子，手执红缨枪，颜色选用了传统的大红和大绿搭配，威风凛凛！', 'SHADOW_PUPPET', 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600', 1, 'APPROVED', 1, 1, 128, 16, 45, 620),
(2, 4, '用青铜纹样做的小镇守护兽', '青铜鼎上的饕餮纹太酷了！我给它加上了像云朵一样的云雷纹，看起来既神秘又神气！', 'BRONZE', 'https://images.unsplash.com/photo-1569783727725-b88d3e230756?w=600', 1, 'APPROVED', 1, 0, 89, 8, 22, 390)
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

-- 11. 非遗地标与文旅活动
INSERT INTO `heritage_landmark` (`id`, `name`, `category`, `address`, `district`, `latitude`, `longitude`, `geofence_radius_meters`, `description`, `cover_url`, `status`) VALUES
(1, '杨柳青古镇民俗文化馆', '民间美术', '天津市西青区杨柳青镇柳口路', '西青区', 39.141200, 117.005300, 800, '杨柳青木版年画发祥地，内有明清老版套印展厅与老艺人亲身传习坊。', 'https://images.unsplash.com/photo-1582560475093-ba66accbc424?w=600', 'ACTIVE'),
(2, '古文化街泥人张美术馆', '民间雕塑', '天津市南开区古文化街宫北84号', '南开区', 39.143800, 117.188200, 500, '展示泥人张六代传人经典杰作，现场可体验古法泥料揉捏与彩绘。', 'https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=600', 'ACTIVE'),
(3, '蓟州独乐寺与盘山非遗工坊', '古建筑与传统技艺', '天津市蓟州区武定街41号', '蓟州区', 40.046500, 117.408900, 1000, '千年辽代木构建筑，配套有蓟州皮影传习社与乡村美育基地。', 'https://images.unsplash.com/photo-1569783727725-b88d3e230756?w=600', 'ACTIVE')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

INSERT INTO `activity` (`id`, `title`, `type`, `landmark_id`, `master_name`, `start_at`, `end_at`, `capacity`, `reserved_count`, `energy_reward`, `status`, `description`) VALUES
(1, '老艺人带你玩转津派皮影——周末乡村美育双师营', 'OFFLINE', 3, '张连春老先生', '2026-09-20 09:30:00', '2026-09-20 16:30:00', 50, 18, 50, 'PUBLISHED', '邀请天津皮影戏非遗传承人面对面手把手教学，体验打磨皮子、雕镂花纹与三签舞台表演！')
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

-- 12. 文创助农商品与SKU
INSERT INTO `product` (`id`, `name`, `category`, `cover_url`, `origin_place`, `story`, `fund_rate_percent`, `status`) VALUES
(1, '杨柳青木版年画DIY亲子拓印套装', 'CULTURAL_CREATIVE', 'https://images.unsplash.com/photo-1582560475093-ba66accbc424?w=400', '西青区杨柳青镇', '采用传统杜梨木复刻老版，配纯手工植物颜料与宣纸，在家即可动手印制年年有余年画！每售出一套，将为乡村小学捐赠15元美育耗材。', 15.00, 'ON_SALE'),
(2, '蓟州盘山磨盘甜柿金秋礼箱（5斤精品装）', 'AGRI_PRODUCT', 'https://images.unsplash.com/photo-1601039641847-7857b994d704?w=400', '蓟州区盘山脚下官庄镇', '蓟州高山阳光日照充足，霜降后自然脱涩，软糯甘甜。销售额10%汇入津韵润乡美育助农公益专项资金。', 10.00, 'ON_SALE')
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

INSERT INTO `product_sku` (`id`, `product_id`, `sku_code`, `name`, `price_cents`, `stock`) VALUES
(1, 1, 'SKU_NLQ_DIY_01', '典雅精装盒（含3版雕模+6色墨水）', 8800, 200),
(2, 2, 'SKU_PERSIMMON_5KG', '高山磨盘柿5斤装（礼盒带防震）', 4990, 500)
ON DUPLICATE KEY UPDATE `name`=VALUES(`name`);

-- 13. 具身智能设备初始台账
INSERT INTO `device` (`id`, `device_code`, `device_name`, `model`, `firmware_version`, `school_id`, `status`, `last_seen_at`) VALUES
(1, 'DEV-SHADOW-BOT-01', '津韵智能皮影表演机器人', 'ROBOT_SHADOW_V1', '1.2.0', 'SCH_JIZHOU_01', 'ONLINE', '2026-09-12 16:50:00')
ON DUPLICATE KEY UPDATE `device_name`=VALUES(`device_name`);

INSERT INTO `device_capability` (`device_id`, `capability_code`, `config_json`) VALUES
(1, 'CAMERA_VISION', '{"resolution":"1080p","fps":30}'),
(1, 'SERVO_ACTUATION', '{"dof":6,"speed":"medium"}'),
(1, 'SPEECH_TTS', '{"voice":"tianjin_dialect_teacher"}')
ON DUPLICATE KEY UPDATE `capability_code`=VALUES(`capability_code`);

-- 14. 首页轮播位配置
INSERT INTO `banner_config` (`id`, `title`, `image_url`, `link_url`, `position`, `sort_no`, `status`) VALUES
(1, '天津皮影双师课堂报名开启！', 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1000', '/activity/1', 'HOME_TOP', 1, 'ACTIVE'),
(2, '庆祝中秋：探寻天津传统泥塑的百年神韵', 'https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=1000', '/course/3', 'HOME_TOP', 2, 'ACTIVE'),
(3, 'AI工坊上新：青铜纹样复原与3D着色', 'https://images.unsplash.com/photo-1569783727725-b88d3e230756?w=1000', '/ai/bronze', 'HOME_TOP', 3, 'ACTIVE')
ON DUPLICATE KEY UPDATE `title`=VALUES(`title`);

-- 15. 运营数据大盘近7天历史数据
INSERT INTO `operation_stat_daily` (`stat_date`, `dau`, `mau`, `new_users`, `course_learn_count`, `ai_generate_count`, `community_post_count`, `order_count`, `order_gmv_cents`, `fund_added_cents`, `device_active_count`) VALUES
('2026-09-06', 1240, 6800, 112, 3450, 480, 52, 28, 245000, 28500, 1),
('2026-09-07', 1320, 7100, 98, 3820, 520, 64, 35, 312000, 34000, 1),
('2026-09-08', 1450, 7400, 140, 4120, 610, 78, 42, 388000, 41500, 1),
('2026-09-09', 1580, 7800, 165, 4650, 740, 92, 50, 442000, 47800, 1),
('2026-09-10', 1820, 8300, 210, 5200, 890, 115, 68, 598000, 64200, 1),
('2026-09-11', 2150, 8900, 280, 6300, 1120, 140, 84, 762000, 82000, 1),
('2026-09-12', 2420, 9600, 315, 7120, 1340, 168, 96, 885000, 95400, 1)
ON DUPLICATE KEY UPDATE `dau`=VALUES(`dau`);

SET FOREIGN_KEY_CHECKS = 1;
