-- Step M062: Swap: make total__dbintel_new the live orders.total
-- Direction: up
-- Findings: SCH-020-bc1e8a52
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of total__dbintel_new is complete; total__dbintel_new matches total
-- Precheck: Backfill of total__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `orders` WHERE `total__dbintel_new` IS NULL AND `total` IS NOT NULL
-- Precheck: total__dbintel_new matches total. Expect 0: SELECT COUNT(*) FROM `orders` WHERE NOT (`total` <=> `total__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `orders` RENAME COLUMN `total` TO `total__dbintel_old`;
ALTER TABLE `orders` RENAME COLUMN `total__dbintel_new` TO `total`;
