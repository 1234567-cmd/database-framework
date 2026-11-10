-- Step M1199: Rename column login_history.logout_time to logout_at
-- Direction: down
-- Findings: SCH-061-147d29fb
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column login_history.logout_time exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'login_history' AND table_schema = DATABASE() AND column_name = 'logout_time'
-- Precheck: Column login_history.logout_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'login_history' AND table_schema = DATABASE() AND column_name = 'logout_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `login_history` RENAME COLUMN `logout_at` TO `logout_time`, ALGORITHM=INPLACE, LOCK=NONE;
