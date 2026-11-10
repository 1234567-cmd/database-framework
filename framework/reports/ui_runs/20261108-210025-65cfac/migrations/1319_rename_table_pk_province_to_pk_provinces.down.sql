-- Step M1319: Rename table pk_province to pk_provinces
-- Direction: down
-- Findings: SCH-055-c9526654
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table pk_province exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'pk_province' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `pk_provinces` TO `pk_province`;
