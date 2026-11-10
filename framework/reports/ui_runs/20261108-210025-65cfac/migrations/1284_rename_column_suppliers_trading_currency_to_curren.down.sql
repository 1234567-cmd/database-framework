-- Step M1284: Rename column suppliers.trading_currency to currency_code_id
-- Direction: down
-- Findings: SCH-058-f5d99e7b
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column suppliers.trading_currency exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'suppliers' AND table_schema = DATABASE() AND column_name = 'trading_currency'
-- Precheck: Column suppliers.currency_code_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'suppliers' AND table_schema = DATABASE() AND column_name = 'currency_code_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `suppliers` RENAME COLUMN `currency_code_id` TO `trading_currency`, ALGORITHM=INPLACE, LOCK=NONE;
