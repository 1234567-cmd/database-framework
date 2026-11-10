-- Step M705: Swap: make deposit_amount__dbintel_new the live customers.deposit_amount
-- Direction: down
-- Findings: SCH-023-615e0542
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of deposit_amount__dbintel_new is complete; deposit_amount__dbintel_new matches deposit_amount
-- Precheck: Backfill of deposit_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customers` WHERE `deposit_amount__dbintel_new` IS NULL AND `deposit_amount` IS NOT NULL
-- Precheck: deposit_amount__dbintel_new matches deposit_amount. Expect 0: SELECT COUNT(*) FROM `customers` WHERE NOT (`deposit_amount` <=> `deposit_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `deposit_amount` TO `deposit_amount__dbintel_new`;
ALTER TABLE `customers` RENAME COLUMN `deposit_amount__dbintel_old` TO `deposit_amount`;
