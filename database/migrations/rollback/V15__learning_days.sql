-- DESTRUCTIVE: back up daily learning history before executing.
-- Application rollback can retain this additive table without losing records.
DROP TABLE IF EXISTS learning_day;
