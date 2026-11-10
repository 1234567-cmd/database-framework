-- Step M070: Swap: make price__dbintel_new the live products.price
-- Direction: up
-- Findings: SCH-020-6d799605
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of price__dbintel_new is complete; price__dbintel_new matches price
-- Precheck: Backfill of price__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `products` WHERE `price__dbintel_new` IS NULL AND `price` IS NOT NULL
-- Precheck: price__dbintel_new matches price. Expect 0: SELECT COUNT(*) FROM `products` WHERE NOT (`price` <=> `price__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `products` RENAME COLUMN `price` TO `price__dbintel_old`;
ALTER TABLE `products` RENAME COLUMN `price__dbintel_new` TO `price`;
