-- Step M1316: Rename table customer_special_handling to customer_special_handlings
-- Direction: down
-- Findings: SCH-055-c51758d5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_special_handling exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_special_handling' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `customer_special_handlings` TO `customer_special_handling`;
