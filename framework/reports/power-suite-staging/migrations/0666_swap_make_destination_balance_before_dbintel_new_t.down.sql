-- Step M666: Swap: make destination_balance_before__dbintel_new the live customer_deposit_transfers.destination_balance_before
-- Direction: down
-- Findings: SCH-023-88e447f4
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of destination_balance_before__dbintel_new is complete; destination_balance_before__dbintel_new matches destination_balance_before
-- Precheck: Backfill of destination_balance_before__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customer_deposit_transfers` WHERE `destination_balance_before__dbintel_new` IS NULL AND `destination_balance_before` IS NOT NULL
-- Precheck: destination_balance_before__dbintel_new matches destination_balance_before. Expect 0: SELECT COUNT(*) FROM `customer_deposit_transfers` WHERE NOT (`destination_balance_before` <=> `destination_balance_before__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_deposit_transfers` RENAME COLUMN `destination_balance_before` TO `destination_balance_before__dbintel_new`;
ALTER TABLE `customer_deposit_transfers` RENAME COLUMN `destination_balance_before__dbintel_old` TO `destination_balance_before`;
