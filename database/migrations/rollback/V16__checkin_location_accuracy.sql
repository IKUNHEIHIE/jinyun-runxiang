-- Drops accuracy/classification metadata. Back up before production rollback.
-- This atomic ALTER fails if repeat visits now exist. Never delete visits just
-- to force rollback; keep the additive schema when rolling application code back.
ALTER TABLE activity_checkin
  ADD UNIQUE KEY uk_user_landmark_date (user_id, landmark_id),
  DROP INDEX idx_user_landmark,
  DROP COLUMN geofence_status,
  DROP COLUMN location_accuracy_meters;
