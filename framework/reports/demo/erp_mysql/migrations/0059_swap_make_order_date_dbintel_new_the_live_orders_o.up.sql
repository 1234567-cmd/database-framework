-- Step M059: Swap: make order_date__dbintel_new the live orders.order_date
-- Direction: up
-- Findings: SCH-031-7a0dc170
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of order_date__dbintel_new is complete; order_date__dbintel_new matches order_date
-- Precheck: Backfill of order_date__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `orders` WHERE `order_date__dbintel_new` IS NULL AND `order_date` IS NOT NULL
-- Precheck: order_date__dbintel_new matches order_date. Expect 0: SELECT COUNT(*) FROM `orders` WHERE NOT (`order_date` <=> `order_date__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` RENAME COLUMN `order_date` TO `order_date__dbintel_old`;
ALTER TABLE `orders` RENAME COLUMN `order_date__dbintel_new` TO `order_date`;
