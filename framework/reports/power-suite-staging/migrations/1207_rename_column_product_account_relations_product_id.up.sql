-- Step M1207: Rename column product_account_relations.product_id to service_type_id
-- Direction: up
-- Findings: SCH-058-7cc782de
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column product_account_relations.product_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'product_account_relations' AND table_schema = DATABASE() AND column_name = 'product_id'
-- Precheck: Column product_account_relations.service_type_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'product_account_relations' AND table_schema = DATABASE() AND column_name = 'service_type_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `product_account_relations` RENAME COLUMN `product_id` TO `service_type_id`, ALGORITHM=INPLACE, LOCK=NONE;
