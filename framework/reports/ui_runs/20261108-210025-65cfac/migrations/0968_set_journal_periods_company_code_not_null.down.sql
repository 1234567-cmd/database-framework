-- Step M968: Set journal_periods.company_code NOT NULL
-- Direction: down
-- Findings: SCH-006-2587b9b7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in journal_periods.company_code (NOT NULL would fail)
-- Precheck: Table journal_periods exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_periods' AND table_schema = DATABASE()
-- Precheck: Column journal_periods.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_periods' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: No NULLs in journal_periods.company_code (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `journal_periods` WHERE `company_code` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_periods` MODIFY COLUMN `company_code` varchar(255) NULL, ALGORITHM=INPLACE, LOCK=NONE;
