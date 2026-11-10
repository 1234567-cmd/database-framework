-- Step M984: Set services.user_id NOT NULL
-- Direction: up
-- Findings: SCH-006-51f7d86e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in services.user_id (NOT NULL would fail)
-- Precheck: Table services exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'services' AND table_schema = DATABASE()
-- Precheck: Column services.user_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'services' AND table_schema = DATABASE() AND column_name = 'user_id'
-- Precheck: No NULLs in services.user_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `services` WHERE `user_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `services` MODIFY COLUMN `user_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
