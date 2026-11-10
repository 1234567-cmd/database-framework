-- Step M1311: Rename column visa_status_history.changed_by to user_id
-- Direction: up
-- Findings: SCH-058-ed6e1c9c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column visa_status_history.changed_by exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_status_history' AND table_schema = DATABASE() AND column_name = 'changed_by'
-- Precheck: Column visa_status_history.user_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_status_history' AND table_schema = DATABASE() AND column_name = 'user_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_status_history` RENAME COLUMN `changed_by` TO `user_id`, ALGORITHM=INPLACE, LOCK=NONE;
