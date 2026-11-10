-- Step M883: Swap: make customer_refund_amount__dbintel_new the live refunds.customer_refund_amount
-- Direction: down
-- Findings: SCH-023-b537a3d6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of customer_refund_amount__dbintel_new is complete; customer_refund_amount__dbintel_new matches customer_refund_amount
-- Precheck: Backfill of customer_refund_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `customer_refund_amount__dbintel_new` IS NULL AND `customer_refund_amount` IS NOT NULL
-- Precheck: customer_refund_amount__dbintel_new matches customer_refund_amount. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE NOT (`customer_refund_amount` <=> `customer_refund_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` RENAME COLUMN `customer_refund_amount` TO `customer_refund_amount__dbintel_new`;
ALTER TABLE `refunds` RENAME COLUMN `customer_refund_amount__dbintel_old` TO `customer_refund_amount`;
