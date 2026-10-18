-- Apply once after V11. Adds an optional idempotency key; preserves existing orders.
ALTER TABLE order_main
  ADD COLUMN client_request_id VARCHAR(64) NULL,
  ADD UNIQUE KEY uk_order_client_request_id (client_request_id);

CREATE TABLE IF NOT EXISTS exchange_item (
  id BIGINT NOT NULL AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  cover_url VARCHAR(500),
  energy_cost INT NOT NULL,
  stock INT NOT NULL DEFAULT 0,
  status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS energy_exchange (
  id BIGINT NOT NULL AUTO_INCREMENT,
  request_id VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  item_id BIGINT NOT NULL,
  item_name VARCHAR(128) NOT NULL,
  energy_cost INT NOT NULL,
  receiver_name VARCHAR(64) NOT NULL,
  receiver_phone VARCHAR(32) NOT NULL,
  receiver_address VARCHAR(255) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'REQUESTED',
  tracking_no VARCHAR(128),
  created_at DATETIME,
  PRIMARY KEY (id),
  UNIQUE KEY uk_exchange_request (request_id),
  KEY ix_energy_exchange_user_id (user_id)
);
