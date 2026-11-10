-- Step M1287: Rename column tcid_users.inactive to is_inactive
-- Direction: up
-- Findings: SCH-060-e6ee5bf3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column tcid_users.inactive exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tcid_users' AND table_schema = DATABASE() AND column_name = 'inactive'
-- Precheck: Column tcid_users.is_inactive does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'tcid_users' AND table_schema = DATABASE() AND column_name = 'is_inactive'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `tcid_users` RENAME COLUMN `inactive` TO `is_inactive`, ALGORITHM=INPLACE, LOCK=NONE;
