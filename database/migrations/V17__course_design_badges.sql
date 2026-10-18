-- Additive, repeatable catalog migration. Keep existing names/rules/artwork.
-- Refuse inconsistent duplicate awards instead of deleting historical data.
SET @ensure_user_badge_unique = IF(
  EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='user_badge' AND INDEX_NAME='uk_user_badge' AND NON_UNIQUE=0),
  'SELECT 1', 'ALTER TABLE user_badge ADD UNIQUE KEY uk_user_badge (user_id, badge_id)');
PREPARE badge_index_change FROM @ensure_user_badge_unique;
EXECUTE badge_index_change;
DEALLOCATE PREPARE badge_index_change;

INSERT INTO badge (code, name, description, icon_url, condition_json) VALUES
('BADGE_COURSE_SHADOW_PUPPET', '皮影匠人', '完成一门已发布皮影课程的全部章节。', '/static/design/bc52c81d0e175da3a49348211b675cf1.png', '{"type":"COURSE_CATEGORY_COMPLETE","category":"SHADOW_PUPPET","target":1}'),
('BADGE_COURSE_BRONZE', '青铜识者', '完成一门已发布青铜课程的全部章节。', '/static/design/4cc6cb3f6ab3a8d4cbdf86b44932bf1f.png', '{"type":"COURSE_CATEGORY_COMPLETE","category":"BRONZE","target":1}'),
('BADGE_COURSE_PAPER_CUTTING', '剪纸巧手', '完成一门已发布剪纸课程的全部章节。', '/static/design/c60d4e28eba132cbad29c60d05c5c637.png', '{"type":"COURSE_CATEGORY_COMPLETE","category":"PAPER_CUTTING","target":1}'),
('BADGE_COURSE_EMBROIDERY', '苏绣传人', '完成一门已发布刺绣课程的全部章节。', '/static/design/4cc84984603424f83df22a2b5254cad5.png', '{"type":"COURSE_CATEGORY_COMPLETE","category":"EMBROIDERY","target":1}'),
('BADGE_COURSE_CERAMICS', '瓷韵匠心', '完成一门已发布瓷器课程的全部章节。', '/static/design/99c4fb71f5018df0bf9aeaa227050cdd.png', '{"type":"COURSE_CATEGORY_COMPLETE","category":"CERAMICS","target":1}'),
('BADGE_HERITAGE_PIONEER', '乡村美育使者', '在非遗地标范围内完成精度可确认的现场打卡。', '/static/images/default_avatar.svg', '{"type":"ONSITE_CHECKIN_COUNT","target":1}'),
('BADGE_WALK_PATHFINDER', '探路者', '在同一上海自然日累计研学60分钟。只计算前台研学时间。', '/static/images/default_avatar.svg', '{"type":"DAILY_WALK_SECONDS","target":3600}')
ON DUPLICATE KEY UPDATE code=badge.code;

-- Backfill only actual stored completion of every chapter of one published
-- course. Empty courses and other users' progress never satisfy the rule.
-- unlocked_at records this migration's award time, not an invented past time.
INSERT INTO user_badge (user_id, badge_id, unlocked_at)
SELECT u.id, b.id, UTC_TIMESTAMP()
FROM sys_user u CROSS JOIN badge b
WHERE b.code IN ('BADGE_COURSE_SHADOW_PUPPET', 'BADGE_COURSE_BRONZE', 'BADGE_COURSE_PAPER_CUTTING', 'BADGE_COURSE_EMBROIDERY', 'BADGE_COURSE_CERAMICS')
AND EXISTS (
  SELECT 1 FROM course c
  WHERE c.status='PUBLISHED' AND c.category=JSON_UNQUOTE(JSON_EXTRACT(b.condition_json, '$.category'))
  AND EXISTS (SELECT 1 FROM course_chapter ch WHERE ch.course_id=c.id)
  AND NOT EXISTS (
    SELECT 1 FROM course_chapter ch WHERE ch.course_id=c.id
    AND NOT EXISTS (
      SELECT 1 FROM learning_progress lp
      WHERE lp.user_id=u.id AND lp.course_id=c.id AND lp.chapter_id=ch.id AND lp.completed=1
    )
  )
)
ON DUPLICATE KEY UPDATE unlocked_at=user_badge.unlocked_at;
