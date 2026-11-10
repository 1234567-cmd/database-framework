-- Step M780: Change type of journal_periods.company_code to varchar(255) (binary compatible)
-- Direction: up
-- Findings: SCH-003-a297008d
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Values in journal_periods.company_code fit length 255
-- Precheck: Table journal_periods exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'journal_periods' AND table_schema = DATABASE()
-- Precheck: Column journal_periods.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'journal_periods' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: Values in journal_periods.company_code fit length 255. Expect 0: SELECT COUNT(*) FROM `journal_periods` WHERE `company_code` IS NOT NULL AND (CHAR_LENGTH(`company_code`) > 255)
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_periods` MODIFY COLUMN `company_code` varchar(255) NULL, ALGORITHM=INPLACE, LOCK=NONE;
