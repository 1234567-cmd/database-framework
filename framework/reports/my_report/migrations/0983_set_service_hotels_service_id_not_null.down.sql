-- Step M983: Set service_hotels.service_id NOT NULL
-- Direction: down
-- Findings: SCH-006-922a1034
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No NULLs in service_hotels.service_id (NOT NULL would fail)
-- Precheck: Table service_hotels exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_hotels' AND table_schema = DATABASE()
-- Precheck: Column service_hotels.service_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hotels' AND table_schema = DATABASE() AND column_name = 'service_id'
-- Precheck: No NULLs in service_hotels.service_id (NOT NULL would fail). Expect 0: SELECT COUNT(*) FROM `service_hotels` WHERE `service_id` IS NULL
-- Note: MySQL needs STRICT_ALL_TABLES or STRICT_TRANS_TABLES for INPLACE and rejects NULLs instead of converting them.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hotels` MODIFY COLUMN `service_id` int NULL, ALGORITHM=INPLACE, LOCK=NONE;
