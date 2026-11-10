-- Step M978: Set refunds.cost_id NOT NULL
-- Direction: down
-- Findings: SCH-006-e0cf087e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in refunds.cost_id (NOT NULL would fail)
-- Precheck: Table refunds exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'refunds' AND table_schema = DATABASE()
-- Precheck: Column refunds.cost_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'refunds' AND table_schema = DATABASE() AND column_name = 'cost_id'
-- Precheck: No NULLs in refunds.cost_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `cost_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` MODIFY COLUMN `cost_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
