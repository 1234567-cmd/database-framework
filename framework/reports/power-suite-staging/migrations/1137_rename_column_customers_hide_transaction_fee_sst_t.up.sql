-- Step M1137: Rename column customers.hide_transaction_fee_sst to is_hide_transaction_fee_sst
-- Direction: up
-- Findings: SCH-060-322926fc
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customers.hide_transaction_fee_sst exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'hide_transaction_fee_sst'
-- Precheck: Column customers.is_hide_transaction_fee_sst does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customers' AND table_schema = DATABASE() AND column_name = 'is_hide_transaction_fee_sst'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `hide_transaction_fee_sst` TO `is_hide_transaction_fee_sst`, ALGORITHM=INPLACE, LOCK=NONE;
