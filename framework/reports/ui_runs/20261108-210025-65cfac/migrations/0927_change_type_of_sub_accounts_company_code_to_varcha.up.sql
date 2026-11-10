-- Step M927: Change type of sub_accounts.company_code to varchar(255) (binary compatible)
-- Direction: up
-- Findings: SCH-003-f696fd6e
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Values in sub_accounts.company_code fit length 255
-- Precheck: Table sub_accounts exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'sub_accounts' AND table_schema = DATABASE()
-- Precheck: Column sub_accounts.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'sub_accounts' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: Values in sub_accounts.company_code fit length 255. Expect 0: SELECT COUNT(*) FROM `sub_accounts` WHERE `company_code` IS NOT NULL AND (CHAR_LENGTH(`company_code`) > 255)
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `sub_accounts` MODIFY COLUMN `company_code` varchar(255) NULL, ALGORITHM=INPLACE, LOCK=NONE;
