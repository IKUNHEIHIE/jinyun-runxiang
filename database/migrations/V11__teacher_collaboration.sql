-- V11: additive teacher collaboration tables. Apply after V10.
CREATE TABLE IF NOT EXISTS lesson_plan_record (
	id BIGINT NOT NULL AUTO_INCREMENT,
	teacher_id BIGINT NOT NULL,
	title VARCHAR(255) NOT NULL,
	grade VARCHAR(64) NOT NULL,
	topic VARCHAR(128) NOT NULL,
	duration_minutes INTEGER NOT NULL,
	content_json JSON NOT NULL,
	source VARCHAR(128) NOT NULL,
	created_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_lesson_plan_record_teacher_id (teacher_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_notice (
	id BIGINT NOT NULL AUTO_INCREMENT,
	class_id BIGINT NOT NULL,
	teacher_id BIGINT NOT NULL,
	title VARCHAR(128) NOT NULL,
	content TEXT NOT NULL,
	created_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_class_notice_class_id (class_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_attendance (
	class_id BIGINT NOT NULL,
	student_id BIGINT NOT NULL,
	day VARCHAR(10) NOT NULL,
	status VARCHAR(16) NOT NULL,
	recorded_by BIGINT NOT NULL,
	updated_at DATETIME,
	PRIMARY KEY (class_id, student_id, day)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_session (
	id BIGINT NOT NULL AUTO_INCREMENT,
	class_id BIGINT NOT NULL,
	host_id BIGINT NOT NULL,
	title VARCHAR(128) NOT NULL,
	stream_url VARCHAR(500),
	status VARCHAR(16) NOT NULL,
	created_at DATETIME,
	ended_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_class_session_class_id (class_id)
) CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS class_message (
	id BIGINT NOT NULL AUTO_INCREMENT,
	session_id BIGINT NOT NULL,
	user_id BIGINT NOT NULL,
	type VARCHAR(16) NOT NULL,
	content VARCHAR(1000) NOT NULL,
	created_at DATETIME,
	PRIMARY KEY (id),
	INDEX ix_class_message_session_id (session_id)
) CHARACTER SET utf8mb4;

