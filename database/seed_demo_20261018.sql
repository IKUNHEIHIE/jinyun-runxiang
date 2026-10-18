SET NAMES utf8mb4;
START TRANSACTION;

INSERT IGNORE INTO community_post
(id,user_id,title,content,category,cover_url,status,is_featured,is_pinned,like_count,comment_count,favorite_count,view_count,created_at,updated_at)
VALUES
(5,1,'沙燕风筝 · 春日放飞','把沙燕风筝的骨架与配色整理成一张观察卡，记录风筝在风里的姿态。','KITE','/static/design/94f0476baa3b9ec92b6579af345fb4ff.png','APPROVED',0,0,6,2,1,48,'2026-10-18 08:02:00','2026-10-18 08:02:00'),
(6,2,'杨柳青年画 · 连年有余','年画里的娃娃、鲤鱼和莲花各有寓意，试着把喜欢的纹样记录下来。','NEW_YEAR_PAINTING','/static/design/75015e1f784cf12dbf311e927c3fcdf4.png','APPROVED',1,0,8,2,2,66,'2026-10-18 08:08:00','2026-10-18 08:08:00'),
(7,1,'皮影净角 · 光影练习','用暖色灯光观察皮影人物的轮廓和关节，记录动作变化。','SHADOW_PUPPET','/static/generated/4db70ada78274a46884e4bdce2de3d41_colored.svg','APPROVED',0,0,5,2,1,39,'2026-10-18 08:14:00','2026-10-18 08:14:00'),
(8,1,'青花缠枝纹 · 器物观察','观察青花瓷瓶的缠枝莲纹，比较器形、留白和蓝色层次。','CERAMICS','/static/design/f3dc231977f584a8034395579dc4fe5b.png','APPROVED',0,0,4,2,1,52,'2026-10-18 08:20:00','2026-10-18 08:20:00');

INSERT IGNORE INTO community_post_detail
(post_id,gallery_json,specifications_json,appreciation_json)
VALUES
(5,'["/static/design/94f0476baa3b9ec92b6579af345fb4ff.png"]','[{"label":"题材","value":"沙燕风筝"},{"label":"记录方式","value":"观察卡"}]','[{"title":"观察风筝","body":"注意骨架、纸面配色和尾羽的节奏。"}]'),
(6,'["/static/design/75015e1f784cf12dbf311e927c3fcdf4.png"]','[{"label":"题材","value":"杨柳青年画"},{"label":"关键字","value":"连年有余"}]','[{"title":"读年画","body":"从娃娃、鲤鱼、莲花等形象理解吉祥寓意。"}]'),
(7,'["/static/generated/4db70ada78274a46884e4bdce2de3d41_colored.svg"]','[{"label":"题材","value":"皮影净角"},{"label":"工艺","value":"皮影雕刻"}]','[{"title":"看光影","body":"观察关节连接处和灯光下的轮廓线。"}]'),
(8,'["/static/design/f3dc231977f584a8034395579dc4fe5b.png"]','[{"label":"题材","value":"青花瓷"},{"label":"纹样","value":"缠枝莲"}]','[{"title":"看青花","body":"比较蓝色浓淡与留白，记录器形比例。"}]');

INSERT IGNORE INTO community_comment (id,post_id,user_id,reply_to_id,content,status,like_count,created_at) VALUES
(4,5,2,NULL,'风筝的配色很清爽，尾羽变化可以再多记录一点。','APPROVED',1,'2026-10-18 08:25:00'),
(5,5,1,NULL,'收到，下次把放飞角度也画下来。','APPROVED',0,'2026-10-18 08:30:00'),
(6,6,1,NULL,'连年有余的鲤鱼纹样很适合做拓印练习。','APPROVED',2,'2026-10-18 08:35:00'),
(7,6,3,NULL,'可以把娃娃和莲花的配色拆开观察。','APPROVED',0,'2026-10-18 08:40:00'),
(8,7,2,NULL,'净角的侧面轮廓很利落，光影层次不错。','APPROVED',1,'2026-10-18 08:45:00'),
(9,7,1,NULL,'谢谢老师，我再试试换一个动作。','APPROVED',0,'2026-10-18 08:48:00'),
(10,8,2,NULL,'青花的蓝色层次记录得很细。','APPROVED',1,'2026-10-18 08:52:00'),
(11,8,1,NULL,'下次会补一张器形比例的草图。','APPROVED',0,'2026-10-18 08:55:00');

UPDATE community_post SET like_count=3, comment_count=3 WHERE id=1;
UPDATE community_post SET like_count=2 WHERE id=2;
UPDATE community_post SET like_count=4 WHERE id=3;
UPDATE community_post SET like_count=3 WHERE id=4;

INSERT IGNORE INTO user_collection (user_id,target_type,target_id,created_at) VALUES
(1,'POST',4,'2026-10-18 09:00:00'),
(1,'POST',5,'2026-10-18 09:01:00'),
(1,'POST',7,'2026-10-18 09:02:00'),
(1,'POST',8,'2026-10-18 09:03:00');

INSERT IGNORE INTO learning_day (user_id,day,created_at) VALUES (1,'2026-10-18','2026-10-18 08:30:00');
UPDATE learning_progress SET last_learned_at='2026-10-18 08:30:00', updated_at='2026-10-18 08:30:00' WHERE id=1;

COMMIT;
