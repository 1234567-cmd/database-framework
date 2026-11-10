-- Step M853: Change type of posting_rules.company_code to varchar(255) (binary compatible)
-- Direction: up
-- Findings: SCH-003-b8aeca5b
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Values in posting_rules.company_code fit length 255
-- Precheck: Table posting_rules exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'posting_rules' AND table_schema = DATABASE()
-- Precheck: Column posting_rules.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'posting_rules' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: Values in posting_rules.company_code fit length 255. Expect 0: SELECT COUNT(*) FROM `posting_rules` WHERE `company_code` IS NOT NULL AND (CHAR_LENGTH(`company_code`) > 255)
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `posting_rules` MODIFY COLUMN `company_code` varchar(255) NULL, ALGORITHM=INPLACE, LOCK=NONE;
