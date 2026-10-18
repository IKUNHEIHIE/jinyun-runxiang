-- Non-destructive code rollback: retain catalog, unique constraint and earned
-- badges. Deleting awarded badges requires a separate reviewed data operation.
SELECT 'V17 catalog and historical awards retained for code rollback' AS rollback_note;
