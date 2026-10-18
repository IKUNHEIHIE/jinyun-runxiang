-- Additive daily learning history. Apply after V14.
-- All stored timestamps are UTC. Learning days use Asia/Shanghai (UTC+8).
-- Recover only dates still present in existing records. Overwritten dates cannot be reconstructed.
CREATE TABLE IF NOT EXISTS learning_day (
  user_id BIGINT NOT NULL,
  day DATE NOT NULL,
  created_at DATETIME,
  PRIMARY KEY (user_id, day)
) CHARACTER SET utf8mb4;

INSERT IGNORE INTO learning_day (user_id, day, created_at)
SELECT user_id, day, UTC_TIMESTAMP()
FROM (
  SELECT user_id, DATE(DATE_ADD(last_learned_at, INTERVAL 8 HOUR)) AS day
  FROM learning_progress WHERE position_seconds > 0 OR completed = 1
  UNION
  SELECT user_id, DATE(DATE_ADD(completed_at, INTERVAL 8 HOUR)) AS day
  FROM learning_progress WHERE completed = 1 AND completed_at IS NOT NULL
  UNION
  SELECT user_id, DATE(DATE_ADD(event_time, INTERVAL 8 HOUR)) AS day
  FROM offline_sync_event
  WHERE event_type = 'PROGRESS_UPDATE'
    AND (CAST(JSON_UNQUOTE(JSON_EXTRACT(payload_json, '$.position_seconds')) AS SIGNED) > 0
         OR JSON_UNQUOTE(JSON_EXTRACT(payload_json, '$.completed')) = 'true')
) AS known_days
WHERE day IS NOT NULL AND day <= DATE(DATE_ADD(UTC_TIMESTAMP(), INTERVAL 8 HOUR));
