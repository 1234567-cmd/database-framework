-- Step M669: Swap: make source_balance_before__dbintel_new the live customer_deposit_transfers.source_balance_before
-- Direction: down
-- Findings: SCH-023-894a1f2e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of source_balance_before__dbintel_new is complete; source_balance_before__dbintel_new matches source_balance_before
-- Precheck: Backfill of source_balance_before__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customer_deposit_transfers` WHERE `source_balance_before__dbintel_new` IS NULL AND `source_balance_before` IS NOT NULL
-- Precheck: source_balance_before__dbintel_new matches source_balance_before. Expect 0: SELECT COUNT(*) FROM `customer_deposit_transfers` WHERE NOT (`source_balance_before` <=> `source_balance_before__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposit_transfers` RENAME COLUMN `source_balance_before` TO `source_balance_before__dbintel_new`;
ALTER TABLE `customer_deposit_transfers` RENAME COLUMN `source_balance_before__dbintel_old` TO `source_balance_before`;
