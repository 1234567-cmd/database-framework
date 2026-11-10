-- Step M1110: Rename column customer_deposit_transfers.je_generated to is_je_generated
-- Direction: down
-- Findings: SCH-060-3800bd9d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column customer_deposit_transfers.je_generated exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposit_transfers' AND table_schema = DATABASE() AND column_name = 'je_generated'
-- Precheck: Column customer_deposit_transfers.is_je_generated does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_deposit_transfers' AND table_schema = DATABASE() AND column_name = 'is_je_generated'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: View refunds_with_conversion references customer_deposit_transfers.je_generated; check its definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposit_transfers` RENAME COLUMN `is_je_generated` TO `je_generated`, ALGORITHM=INPLACE, LOCK=NONE;
