-- Apply once to an existing V1-V8 database; back up before migration.
-- The column helper makes upgrades safe when some fields already exist.
DROP PROCEDURE IF EXISTS jinyun_add_column;
DELIMITER $$
CREATE PROCEDURE jinyun_add_column(IN table_name_arg VARCHAR(64), IN column_name_arg VARCHAR(64), IN definition_arg VARCHAR(255))
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = table_name_arg AND column_name = column_name_arg) THEN
        SET @ddl = CONCAT('ALTER TABLE `', table_name_arg, '` ADD COLUMN `', column_name_arg, '` ', definition_arg);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;
CALL jinyun_add_column('sys_user', 'token_version', 'INT NOT NULL DEFAULT 0');
CALL jinyun_add_column('community_post', 'is_co_creation', 'BOOLEAN NOT NULL DEFAULT FALSE');
CALL jinyun_add_column('community_post', 'co_creator_name', 'VARCHAR(64) NULL');
CALL jinyun_add_column('community_post', 'co_creator_school', 'VARCHAR(128) NULL');
CALL jinyun_add_column('community_post', 'rural_author_name', 'VARCHAR(64) NULL');
CALL jinyun_add_column('community_post', 'rural_school', 'VARCHAR(128) NULL');
CALL jinyun_add_column('community_post', 'rural_original_url', 'VARCHAR(500) NULL');
DROP PROCEDURE jinyun_add_column;


-- Additional application tables (also available in V9).
CREATE TABLE IF NOT EXISTS sys_config (
	id INTEGER NOT NULL AUTO_INCREMENT,
	config_key VARCHAR(64) NOT NULL,
	config_value TEXT NOT NULL,
	description VARCHAR(255),
	updated_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE (config_key)
);

CREATE TABLE IF NOT EXISTS folk_festival (
	id BIGINT NOT NULL AUTO_INCREMENT,
	title VARCHAR(128) NOT NULL,
	solar_date VARCHAR(32),
	lunar_date VARCHAR(32) NOT NULL,
	category VARCHAR(64),
	tag VARCHAR(64),
	customs VARCHAR(255),
	description TEXT,
	cover_url VARCHAR(500),
	status VARCHAR(16),
	sort_order INTEGER,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS philanthropy_supply (
	id BIGINT NOT NULL AUTO_INCREMENT,
	school_name VARCHAR(128) NOT NULL,
	district VARCHAR(64) NOT NULL,
	materials_name VARCHAR(128) NOT NULL,
	quantity INTEGER NOT NULL,
	unit VARCHAR(16),
	beneficiary_students INTEGER,
	delivered_date VARCHAR(32),
	batch_no VARCHAR(64),
	photo_url VARCHAR(500),
	status VARCHAR(16),
	created_at DATETIME,
	PRIMARY KEY (id)
);
