-- Step M1325: Rename table system_date_setting to system_date_settings
-- Direction: down
-- Findings: SCH-055-103a2069
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table system_date_setting exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'system_date_setting' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `system_date_settings` TO `system_date_setting`;
