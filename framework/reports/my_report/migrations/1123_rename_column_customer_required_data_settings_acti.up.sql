-- Step M1123: Rename column customer_required_data_settings.active to is_active
-- Direction: up
-- Findings: SCH-060-f8ab8296
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data_settings.active exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_settings' AND table_schema = DATABASE() AND column_name = 'active'
-- Precheck: Column customer_required_data_settings.is_active does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_settings' AND table_schema = DATABASE() AND column_name = 'is_active'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_settings` RENAME COLUMN `active` TO `is_active`, ALGORITHM=INPLACE, LOCK=NONE;
