-- Step M960: Set debit_notes.base_currency_id NOT NULL
-- Direction: up
-- Findings: SCH-006-922d9b87
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in debit_notes.base_currency_id (NOT NULL would fail)
-- Precheck: Table debit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'debit_notes' AND table_schema = DATABASE()
-- Precheck: Column debit_notes.base_currency_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'debit_notes' AND table_schema = DATABASE() AND column_name = 'base_currency_id'
-- Precheck: No NULLs in debit_notes.base_currency_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `debit_notes` WHERE `base_currency_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` MODIFY COLUMN `base_currency_id` int NOT NULL DEFAULT '110', ALGORITHM=INPLACE, LOCK=NONE;
