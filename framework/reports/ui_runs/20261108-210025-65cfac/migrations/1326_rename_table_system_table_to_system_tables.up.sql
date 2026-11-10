-- Step M1326: Rename table system_table to system_tables
-- Direction: up
-- Findings: SCH-055-a21307e2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table system_table exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'system_table' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `system_table` TO `system_tables`;
