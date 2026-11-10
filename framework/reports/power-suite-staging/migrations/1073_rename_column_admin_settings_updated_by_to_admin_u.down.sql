-- Step M1073: Rename column admin_settings.updated_by to admin_user_id
-- Direction: down
-- Findings: SCH-058-11b311e8
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column admin_settings.updated_by exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'admin_settings' AND table_schema = DATABASE() AND column_name = 'updated_by'
-- Precheck: Column admin_settings.admin_user_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'admin_settings' AND table_schema = DATABASE() AND column_name = 'admin_user_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `admin_settings` RENAME COLUMN `admin_user_id` TO `updated_by`, ALGORITHM=INPLACE, LOCK=NONE;
