-- Step M696: Swap: make acc_open_date__dbintel_new the live customers.acc_open_date
-- Direction: up
-- Findings: SCH-031-9dff568c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of acc_open_date__dbintel_new is complete; acc_open_date__dbintel_new matches acc_open_date
-- Precheck: Backfill of acc_open_date__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customers` WHERE `acc_open_date__dbintel_new` IS NULL AND `acc_open_date` IS NOT NULL
-- Precheck: acc_open_date__dbintel_new matches acc_open_date. Expect 0: SELECT COUNT(*) FROM `customers` WHERE NOT (`acc_open_date` <=> `acc_open_date__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `acc_open_date` TO `acc_open_date__dbintel_old`;
ALTER TABLE `customers` RENAME COLUMN `acc_open_date__dbintel_new` TO `acc_open_date`;
