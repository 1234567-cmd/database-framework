-- Step M841: Swap: make amount__dbintel_new the live payment_settlement_overpayments.amount
-- Direction: up
-- Findings: SCH-023-d30fe173
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of amount__dbintel_new is complete; amount__dbintel_new matches amount
-- Precheck: Backfill of amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `payment_settlement_overpayments` WHERE `amount__dbintel_new` IS NULL AND `amount` IS NOT NULL
-- Precheck: amount__dbintel_new matches amount. Expect 0: SELECT COUNT(*) FROM `payment_settlement_overpayments` WHERE NOT (`amount` <=> `amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_overpayments` RENAME COLUMN `amount` TO `amount__dbintel_old`;
ALTER TABLE `payment_settlement_overpayments` RENAME COLUMN `amount__dbintel_new` TO `amount`;
