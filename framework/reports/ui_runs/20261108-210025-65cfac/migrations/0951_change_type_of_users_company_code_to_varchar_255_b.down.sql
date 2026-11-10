-- Step M951: Change type of users.company_code to varchar(255) (binary compatible)
-- Direction: down
-- Findings: SCH-003-fcff1bbb
-- Destructive: False. Reversible: True. Data loss risk: low. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Values in users.company_code fit length 255
-- Precheck: Table users exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users' AND table_schema = DATABASE()
-- Precheck: Column users.company_code exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'users' AND table_schema = DATABASE() AND column_name = 'company_code'
-- Precheck: Values in users.company_code fit length 255. Expect 0: SELECT COUNT(*) FROM `users` WHERE `company_code` IS NOT NULL AND (CHAR_LENGTH(`company_code`) > 255)
-- Note: Rollback converts back to the original type and fails if newer values no longer fit it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `users` MODIFY COLUMN `company_code` varchar(200) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
