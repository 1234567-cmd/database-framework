-- Step M1122: Rename column customer_required_data_profiles.product_code_id to service_type_id
-- Direction: up
-- Findings: SCH-058-a6beac40
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_required_data_profiles.product_code_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'product_code_id'
-- Precheck: Column customer_required_data_profiles.service_type_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'service_type_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_profiles` RENAME COLUMN `product_code_id` TO `service_type_id`, ALGORITHM=INPLACE, LOCK=NONE;
