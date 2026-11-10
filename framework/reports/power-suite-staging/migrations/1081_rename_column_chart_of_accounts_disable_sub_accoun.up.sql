-- Step M1081: Rename column chart_of_accounts.disable_sub_account to is_disable_sub_account
-- Direction: up
-- Findings: SCH-060-5637493b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column chart_of_accounts.disable_sub_account exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'chart_of_accounts' AND table_schema = DATABASE() AND column_name = 'disable_sub_account'
-- Precheck: Column chart_of_accounts.is_disable_sub_account does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'chart_of_accounts' AND table_schema = DATABASE() AND column_name = 'is_disable_sub_account'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `chart_of_accounts` RENAME COLUMN `disable_sub_account` TO `is_disable_sub_account`, ALGORITHM=INPLACE, LOCK=NONE;
