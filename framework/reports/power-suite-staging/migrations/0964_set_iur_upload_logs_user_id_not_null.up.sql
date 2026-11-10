-- Step M964: Set iur_upload_logs.user_id NOT NULL
-- Direction: up
-- Findings: SCH-006-a04e8bbf
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in iur_upload_logs.user_id (NOT NULL would fail)
-- Precheck: Table iur_upload_logs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_upload_logs' AND table_schema = DATABASE()
-- Precheck: Column iur_upload_logs.user_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iur_upload_logs' AND table_schema = DATABASE() AND column_name = 'user_id'
-- Precheck: No NULLs in iur_upload_logs.user_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `iur_upload_logs` WHERE `user_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_upload_logs` MODIFY COLUMN `user_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
