-- Step M980: Set refunds.service_id NOT NULL
-- Direction: up
-- Findings: SCH-006-92b87455
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in refunds.service_id (NOT NULL would fail)
-- Precheck: Table refunds exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'refunds' AND table_schema = DATABASE()
-- Precheck: Column refunds.service_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'refunds' AND table_schema = DATABASE() AND column_name = 'service_id'
-- Precheck: No NULLs in refunds.service_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `service_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` MODIFY COLUMN `service_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
