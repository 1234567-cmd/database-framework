-- Step M1124: Rename column customer_required_data_settings.mandatory to is_mandatory
-- Direction: down
-- Findings: SCH-060-ee81b89a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data_settings.mandatory exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_settings' AND table_schema = DATABASE() AND column_name = 'mandatory'
-- Precheck: Column customer_required_data_settings.is_mandatory does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_settings' AND table_schema = DATABASE() AND column_name = 'is_mandatory'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_settings` RENAME COLUMN `is_mandatory` TO `mandatory`, ALGORITHM=INPLACE, LOCK=NONE;
