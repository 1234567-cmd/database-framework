-- Step M1317: Rename table intake_cache to intake_caches
-- Direction: down
-- Findings: SCH-055-a6be1db7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table intake_cache exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'intake_cache' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `intake_caches` TO `intake_cache`;
