-- Step M936: Swap: make current_amount__dbintel_new the live supplier_deposits.current_amount
-- Direction: down
-- Findings: SCH-023-6a5ecd51
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of current_amount__dbintel_new is complete; current_amount__dbintel_new matches current_amount
-- Precheck: Backfill of current_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `supplier_deposits` WHERE `current_amount__dbintel_new` IS NULL AND `current_amount` IS NOT NULL
-- Precheck: current_amount__dbintel_new matches current_amount. Expect 0: SELECT COUNT(*) FROM `supplier_deposits` WHERE NOT (`current_amount` <=> `current_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `supplier_deposits` RENAME COLUMN `current_amount` TO `current_amount__dbintel_new`;
ALTER TABLE `supplier_deposits` RENAME COLUMN `current_amount__dbintel_old` TO `current_amount`;
