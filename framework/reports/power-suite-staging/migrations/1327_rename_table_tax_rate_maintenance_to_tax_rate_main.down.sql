-- Step M1327: Rename table tax_rate_maintenance to tax_rate_maintenances
-- Direction: down
-- Findings: SCH-055-8012e616
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table tax_rate_maintenance exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tax_rate_maintenance' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `tax_rate_maintenances` TO `tax_rate_maintenance`;
