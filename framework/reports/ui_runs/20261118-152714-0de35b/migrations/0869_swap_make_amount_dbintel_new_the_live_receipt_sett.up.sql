-- Step M869: Swap: make amount__dbintel_new the live receipt_settlement_transfers.amount
-- Direction: up
-- Findings: SCH-023-61bd802e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of amount__dbintel_new is complete; amount__dbintel_new matches amount
-- Precheck: Backfill of amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `receipt_settlement_transfers` WHERE `amount__dbintel_new` IS NULL AND `amount` IS NOT NULL
-- Precheck: amount__dbintel_new matches amount. Expect 0: SELECT COUNT(*) FROM `receipt_settlement_transfers` WHERE NOT (`amount` <=> `amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `receipt_settlement_transfers` RENAME COLUMN `amount` TO `amount__dbintel_old`;
ALTER TABLE `receipt_settlement_transfers` RENAME COLUMN `amount__dbintel_new` TO `amount`;
