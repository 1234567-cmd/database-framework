-- Step M794: Swap: make transaction_fee_max_amount__dbintel_new the live maintenance_fee_groups.transaction_fee_max_amount
-- Direction: down
-- Findings: SCH-032-3d03ea7e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of transaction_fee_max_amount__dbintel_new is complete; transaction_fee_max_amount__dbintel_new matches transaction_fee_max_amount
-- Precheck: Backfill of transaction_fee_max_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE `transaction_fee_max_amount__dbintel_new` IS NULL AND `transaction_fee_max_amount` IS NOT NULL
-- Precheck: transaction_fee_max_amount__dbintel_new matches transaction_fee_max_amount. Expect 0: SELECT COUNT(*) FROM `maintenance_fee_groups` WHERE NOT (`transaction_fee_max_amount` <=> `transaction_fee_max_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `transaction_fee_max_amount` TO `transaction_fee_max_amount__dbintel_new`;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `transaction_fee_max_amount__dbintel_old` TO `transaction_fee_max_amount`;
