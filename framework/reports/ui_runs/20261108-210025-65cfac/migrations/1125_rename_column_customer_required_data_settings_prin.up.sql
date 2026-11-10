-- Step M1125: Rename column customer_required_data_settings.print to is_print
-- Direction: up
-- Findings: SCH-060-45d2b871
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data_settings.print exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_settings' AND table_schema = DATABASE() AND column_name = 'print'
-- Precheck: Column customer_required_data_settings.is_print does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_settings' AND table_schema = DATABASE() AND column_name = 'is_print'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_settings` RENAME COLUMN `print` TO `is_print`, ALGORITHM=INPLACE, LOCK=NONE;
