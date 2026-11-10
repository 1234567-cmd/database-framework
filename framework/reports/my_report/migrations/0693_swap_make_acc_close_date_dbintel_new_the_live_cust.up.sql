-- Step M693: Swap: make acc_close_date__dbintel_new the live customers.acc_close_date
-- Direction: up
-- Findings: SCH-031-188ab9df
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of acc_close_date__dbintel_new is complete; acc_close_date__dbintel_new matches acc_close_date
-- Precheck: Backfill of acc_close_date__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customers` WHERE `acc_close_date__dbintel_new` IS NULL AND `acc_close_date` IS NOT NULL
-- Precheck: acc_close_date__dbintel_new matches acc_close_date. Expect 0: SELECT COUNT(*) FROM `customers` WHERE NOT (`acc_close_date` <=> `acc_close_date__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `acc_close_date` TO `acc_close_date__dbintel_old`;
ALTER TABLE `customers` RENAME COLUMN `acc_close_date__dbintel_new` TO `acc_close_date`;
