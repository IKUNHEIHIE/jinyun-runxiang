-- Code rollback keeps nullable request identities and the unique constraint.
-- Older application code ignores these columns. Do not erase saved plans or retry identities.
SELECT 1;
