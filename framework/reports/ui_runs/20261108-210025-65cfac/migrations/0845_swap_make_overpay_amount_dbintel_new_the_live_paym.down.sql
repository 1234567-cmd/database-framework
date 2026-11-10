-- Step M845: Swap: make overpay_amount__dbintel_new the live payment_settlement_payments.overpay_amount
-- Direction: down
-- Findings: SCH-023-36f8b67d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of overpay_amount__dbintel_new is complete; overpay_amount__dbintel_new matches overpay_amount
-- Precheck: Backfill of overpay_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `payment_settlement_payments` WHERE `overpay_amount__dbintel_new` IS NULL AND `overpay_amount` IS NOT NULL
-- Precheck: overpay_amount__dbintel_new matches overpay_amount. Expect 0: SELECT COUNT(*) FROM `payment_settlement_payments` WHERE NOT (`overpay_amount` <=> `overpay_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_payments` RENAME COLUMN `overpay_amount` TO `overpay_amount__dbintel_new`;
ALTER TABLE `payment_settlement_payments` RENAME COLUMN `overpay_amount__dbintel_old` TO `overpay_amount`;
