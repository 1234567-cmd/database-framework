-- Step M1198: Rename column login_history.login_time to login_at
-- Direction: up
-- Findings: SCH-061-c6108f1f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column login_history.login_time exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'login_history' AND table_schema = DATABASE() AND column_name = 'login_time'
-- Precheck: Column login_history.login_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'login_history' AND table_schema = DATABASE() AND column_name = 'login_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `login_history` RENAME COLUMN `login_time` TO `login_at`, ALGORITHM=INPLACE, LOCK=NONE;
