-- Step M1196: Rename column intake_trackers.auto_assigned to is_auto_assigned
-- Direction: down
-- Findings: SCH-060-d99060b7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column intake_trackers.auto_assigned exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'intake_trackers' AND table_schema = DATABASE() AND column_name = 'auto_assigned'
-- Precheck: Column intake_trackers.is_auto_assigned does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'intake_trackers' AND table_schema = DATABASE() AND column_name = 'is_auto_assigned'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `intake_trackers` RENAME COLUMN `is_auto_assigned` TO `auto_assigned`, ALGORITHM=INPLACE, LOCK=NONE;
