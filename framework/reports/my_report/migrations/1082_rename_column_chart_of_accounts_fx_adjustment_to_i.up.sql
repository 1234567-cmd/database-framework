-- Step M1082: Rename column chart_of_accounts.fx_adjustment to is_fx_adjustment
-- Direction: up
-- Findings: SCH-060-a7ab7a38
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column chart_of_accounts.fx_adjustment exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'chart_of_accounts' AND table_schema = DATABASE() AND column_name = 'fx_adjustment'
-- Precheck: Column chart_of_accounts.is_fx_adjustment does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'chart_of_accounts' AND table_schema = DATABASE() AND column_name = 'is_fx_adjustment'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `chart_of_accounts` RENAME COLUMN `fx_adjustment` TO `is_fx_adjustment`, ALGORITHM=INPLACE, LOCK=NONE;
