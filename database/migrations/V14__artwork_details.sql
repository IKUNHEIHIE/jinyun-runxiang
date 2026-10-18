-- Additive artwork gallery/metadata and comment likes. Apply after V13.
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
