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
  INDEX ix_user_feedback_user_id (user_id)
) CHARACTER SET utf8mb4;
