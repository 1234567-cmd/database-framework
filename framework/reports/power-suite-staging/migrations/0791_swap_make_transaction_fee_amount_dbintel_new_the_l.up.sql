-- Step M791: Swap: make transaction_fee_amount__dbintel_new the live maintenance_fee_groups.transaction_fee_amount
-- Direction: up
-- Findings: SCH-032-559100a5
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of transaction_fee_amount__dbintel_new is complete; transaction_fee_amount__dbintel_new matches transaction_fee_amount
-- Precheck: Backfill of transaction_fee_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE `transaction_fee_amount__dbintel_new` IS NULL AND `transaction_fee_amount` IS NOT NULL
-- Precheck: transaction_fee_amount__dbintel_new matches transaction_fee_amount. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE NOT (`transaction_fee_amount` <=> `transaction_fee_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `transaction_fee_amount` TO `transaction_fee_amount__dbintel_old`;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `transaction_fee_amount__dbintel_new` TO `transaction_fee_amount`;
