-- Apply once after V15. Existing rows retain their historical classification.
-- New records persist the accuracy and classification used at submission time.
ALTER TABLE activity_checkin
  ADD COLUMN location_accuracy_meters DECIMAL(10,2) NULL,
  ADD COLUMN geofence_status VARCHAR(16) NULL;

-- Multiple visits are retained; growth_event's unique event reference prevents
-- repeated rewards. Some ORM-created databases never had the legacy index.
SET @drop_old_checkin_index = IF(
  EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_checkin' AND INDEX_NAME='uk_user_landmark_date'),
  'ALTER TABLE activity_checkin DROP INDEX uk_user_landmark_date', 'SELECT 1');
PREPARE checkin_index_change FROM @drop_old_checkin_index;
EXECUTE checkin_index_change;
DEALLOCATE PREPARE checkin_index_change;

SET @add_checkin_lookup_index = IF(
  EXISTS(SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='activity_checkin' AND INDEX_NAME='idx_user_landmark'),
  'SELECT 1', 'ALTER TABLE activity_checkin ADD INDEX idx_user_landmark (user_id, landmark_id)');
PREPARE checkin_index_change FROM @add_checkin_lookup_index;
EXECUTE checkin_index_change;
DEALLOCATE PREPARE checkin_index_change;
