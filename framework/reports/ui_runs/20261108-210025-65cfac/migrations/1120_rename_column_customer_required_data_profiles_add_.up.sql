-- Step M1120: Rename column customer_required_data_profiles.add_to_all_profiles to is_add_to_all_profiles
-- Direction: up
-- Findings: SCH-060-e503e77a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data_profiles.add_to_all_profiles exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'add_to_all_profiles'
-- Precheck: Column customer_required_data_profiles.is_add_to_all_profiles does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'is_add_to_all_profiles'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_profiles` RENAME COLUMN `add_to_all_profiles` TO `is_add_to_all_profiles`, ALGORITHM=INPLACE, LOCK=NONE;
