-- DESTRUCTIVE ROLLBACK: back up all five tables and confirm before executing.
-- Application rollback can leave these additive tables intact without data loss.
DROP TABLE IF EXISTS user_feedback;
DROP TABLE IF EXISTS course_rating;
DROP TABLE IF EXISTS user_follow;
DROP TABLE IF EXISTS user_collection;
DROP TABLE IF EXISTS heritage_entry;
