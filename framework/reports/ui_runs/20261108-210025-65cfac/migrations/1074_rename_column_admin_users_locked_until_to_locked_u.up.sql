-- Step M1074: Rename column admin_users.locked_until to locked_until_at
-- Direction: up
-- Findings: SCH-061-92ce1220
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column admin_users.locked_until exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'admin_users' AND table_schema = DATABASE() AND column_name = 'locked_until'
-- Precheck: Column admin_users.locked_until_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'admin_users' AND table_schema = DATABASE() AND column_name = 'locked_until_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `admin_users` RENAME COLUMN `locked_until` TO `locked_until_at`, ALGORITHM=INPLACE, LOCK=NONE;
