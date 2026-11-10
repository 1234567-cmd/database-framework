-- Step M963: Set hotel_rate_breakdowns.service_id NOT NULL
-- Direction: up
-- Findings: SCH-006-3fbf63be
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in hotel_rate_breakdowns.service_id (NOT NULL would fail)
-- Precheck: Table hotel_rate_breakdowns exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'hotel_rate_breakdowns' AND table_schema = DATABASE()
-- Precheck: Column hotel_rate_breakdowns.service_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_rate_breakdowns' AND table_schema = DATABASE() AND column_name = 'service_id'
-- Precheck: No NULLs in hotel_rate_breakdowns.service_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `hotel_rate_breakdowns` WHERE `service_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_rate_breakdowns` MODIFY COLUMN `service_id` int NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
