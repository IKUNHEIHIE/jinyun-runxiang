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
