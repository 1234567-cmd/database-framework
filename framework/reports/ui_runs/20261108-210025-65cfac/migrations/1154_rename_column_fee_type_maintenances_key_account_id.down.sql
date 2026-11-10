-- Step M1154: Rename column fee_type_maintenances.key_account_id to gl_settle_account_id
-- Direction: down
-- Findings: SCH-058-d69db431
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column fee_type_maintenances.key_account_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_type_maintenances' AND table_schema = DATABASE() AND column_name = 'key_account_id'
-- Precheck: Column fee_type_maintenances.gl_settle_account_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_type_maintenances' AND table_schema = DATABASE() AND column_name = 'gl_settle_account_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_type_maintenances` RENAME COLUMN `gl_settle_account_id` TO `key_account_id`, ALGORITHM=INPLACE, LOCK=NONE;
