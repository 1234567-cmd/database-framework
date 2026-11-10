-- Step M1318: Rename table migration_test to migration_tests
-- Direction: down
-- Findings: SCH-055-63b41247
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table migration_test exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'migration_test' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `migration_tests` TO `migration_test`;
