-- Step M1320: Rename table report_group to report_groups
-- Direction: down
-- Findings: SCH-055-511ab3f7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table report_group exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'report_group' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `report_groups` TO `report_group`;
