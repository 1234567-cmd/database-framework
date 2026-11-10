-- Step M089: Add check constraint check_products_status on products
-- Direction: up
-- Findings: SCH-046-9518a10a
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: No rows violate status IN ('active', 'discontinued')
-- Precheck: Table products exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'products' AND table_schema = DATABASE()
-- Precheck: No rows violate status IN ('active', 'discontinued'). Expect 0: SELECT COUNT(*) FROM `products` WHERE NOT (status IN ('active', 'discontinued'))
-- Note: MySQL enforces CHECK from 8.0.16; earlier versions parse and ignore it.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `products` ADD CONSTRAINT `check_products_status` CHECK (status IN ('active', 'discontinued'));
