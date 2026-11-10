-- Step M1236: Rename column service_hajj_transports.drop to drop_value
-- Direction: down
-- Findings: SCH-050-e1897dfd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_hajj_transports.drop exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_transports' AND table_schema = DATABASE() AND column_name = 'drop'
-- Precheck: Column service_hajj_transports.drop_value does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_transports' AND table_schema = DATABASE() AND column_name = 'drop_value'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hajj_transports` RENAME COLUMN `drop_value` TO `drop`, ALGORITHM=INPLACE, LOCK=NONE;
