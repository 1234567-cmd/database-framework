-- Step M1121: Rename column customer_required_data_profiles.mandatory to is_mandatory
-- Direction: up
-- Findings: SCH-060-bd7cf9d5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data_profiles.mandatory exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'mandatory'
-- Precheck: Column customer_required_data_profiles.is_mandatory does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'is_mandatory'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_profiles` RENAME COLUMN `mandatory` TO `is_mandatory`, ALGORITHM=INPLACE, LOCK=NONE;
