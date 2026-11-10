-- Step M1268: Rename column special_account_maintenances.adj_account to is_adj_account
-- Direction: up
-- Findings: SCH-060-449fad97
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column special_account_maintenances.adj_account exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'special_account_maintenances' AND table_schema = DATABASE() AND column_name = 'adj_account'
-- Precheck: Column special_account_maintenances.is_adj_account does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'special_account_maintenances' AND table_schema = DATABASE() AND column_name = 'is_adj_account'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `special_account_maintenances` RENAME COLUMN `adj_account` TO `is_adj_account`, ALGORITHM=INPLACE, LOCK=NONE;
