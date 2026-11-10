-- Step M1321: Rename table sales_id to sales_ids
-- Direction: down
-- Findings: SCH-055-e36ee1b6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table sales_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'sales_id' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Foreign key from credit_notes references sales_id.
-- Dependency risk: Foreign key from customers references sales_id.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `sales_ids` TO `sales_id`;
