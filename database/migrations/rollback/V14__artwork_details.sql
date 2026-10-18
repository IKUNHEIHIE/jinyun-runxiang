-- DESTRUCTIVE: back up artwork metadata and comment likes before executing.
-- Application rollback can retain these additive tables without losing records.
DROP TABLE IF EXISTS community_comment_like;
DROP TABLE IF EXISTS community_post_detail;
