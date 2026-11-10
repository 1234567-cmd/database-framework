-- Step M957: Set credit_notes.base_currency_id NOT NULL
-- Direction: down
-- Findings: SCH-006-20b16e74
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in credit_notes.base_currency_id (NOT NULL would fail)
-- Precheck: Table credit_notes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'credit_notes' AND table_schema = DATABASE()
-- Precheck: Column credit_notes.base_currency_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'credit_notes' AND table_schema = DATABASE() AND column_name = 'base_currency_id'
-- Precheck: No NULLs in credit_notes.base_currency_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `base_currency_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` MODIFY COLUMN `base_currency_id` int NULL DEFAULT '110', ALGORITHM=INPLACE, LOCK=NONE;
