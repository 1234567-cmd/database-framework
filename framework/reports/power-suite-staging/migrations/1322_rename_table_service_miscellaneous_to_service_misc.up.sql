-- Step M1322: Rename table service_miscellaneous to service_miscellaneouss
-- Direction: up
-- Findings: SCH-055-32c10828
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_miscellaneous exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_miscellaneous' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `service_miscellaneous` TO `service_miscellaneouss`;
