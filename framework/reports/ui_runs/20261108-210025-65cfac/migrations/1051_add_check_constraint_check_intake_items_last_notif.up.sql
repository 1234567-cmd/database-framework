-- Step M1051: Add check constraint check_intake_items_last_notified_status on intake_items
-- Direction: up
-- Findings: SCH-046-6d1a3b9d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate last_notified_status IN ('accepted', 'duplicate', 'pending')
-- Precheck: Table intake_items exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'intake_items' AND table_schema = DATABASE()
-- Precheck: No rows violate last_notified_status IN ('accepted', 'duplicate', 'pending'). Expect 0: SELECT COUNT(*) FROM `intake_items` WHERE NOT (last_notified_status IN ('accepted', 'duplicate', 'pending'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `intake_items` ADD CONSTRAINT `check_intake_items_last_notified_status` CHECK (last_notified_status IN ('accepted', 'duplicate', 'pending'));
