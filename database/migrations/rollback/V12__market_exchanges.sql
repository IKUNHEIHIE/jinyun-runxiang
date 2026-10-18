-- DESTRUCTIVE: back up exchange records and idempotency keys; confirm before execution.
-- Application rollback can leave these additive resources intact.
DROP TABLE IF EXISTS energy_exchange;
DROP TABLE IF EXISTS exchange_item;
ALTER TABLE order_main DROP INDEX uk_order_client_request_id, DROP COLUMN client_request_id;
