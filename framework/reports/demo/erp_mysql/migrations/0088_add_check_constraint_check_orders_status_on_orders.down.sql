-- Step M088: Add check constraint check_orders_status on orders
-- Direction: down
-- Findings: SCH-046-7cccb025
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('cancelled', 'open', 'shipped')
-- Precheck: Table orders exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'orders' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('cancelled', 'open', 'shipped'). Expect 0: SELECT COUNT(*) FROM `orders` WHERE NOT (status IN ('cancelled', 'open', 'shipped'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` DROP CHECK `check_orders_status`;
