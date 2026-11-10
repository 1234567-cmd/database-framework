-- Step M060: Contract: drop the old orders.order_date__dbintel_old
-- Direction: up
-- Findings: SCH-031-7a0dc170
-- Destructive: True. Reversible: False. Data loss risk: high. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires a verified backup first.
-- Precheck: Column orders.order_date__dbintel_old exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'orders' AND table_schema = DATABASE() AND column_name = 'order_date__dbintel_old'
-- Note: Run only after the new column has been verified in production through at least one release (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` DROP COLUMN `order_date__dbintel_old`, ALGORITHM=INPLACE, LOCK=NONE;
