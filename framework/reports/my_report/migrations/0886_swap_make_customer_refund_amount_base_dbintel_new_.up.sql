-- Step M886: Swap: make customer_refund_amount_base__dbintel_new the live refunds.customer_refund_amount_base
-- Direction: up
-- Findings: SCH-023-1c597b8f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of customer_refund_amount_base__dbintel_new is complete; customer_refund_amount_base__dbintel_new matches customer_refund_amount_base
-- Precheck: Backfill of customer_refund_amount_base__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `customer_refund_amount_base__dbintel_new` IS NULL AND `customer_refund_amount_base` IS NOT NULL
-- Precheck: customer_refund_amount_base__dbintel_new matches customer_refund_amount_base. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE NOT (`customer_refund_amount_base` <=> `customer_refund_amount_base__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` RENAME COLUMN `customer_refund_amount_base` TO `customer_refund_amount_base__dbintel_old`;
ALTER TABLE `refunds` RENAME COLUMN `customer_refund_amount_base__dbintel_new` TO `customer_refund_amount_base`;
