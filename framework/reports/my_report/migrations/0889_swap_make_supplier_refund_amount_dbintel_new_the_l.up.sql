-- Step M889: Swap: make supplier_refund_amount__dbintel_new the live refunds.supplier_refund_amount
-- Direction: up
-- Findings: SCH-023-35e6dbd7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of supplier_refund_amount__dbintel_new is complete; supplier_refund_amount__dbintel_new matches supplier_refund_amount
-- Precheck: Backfill of supplier_refund_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `supplier_refund_amount__dbintel_new` IS NULL AND `supplier_refund_amount` IS NOT NULL
-- Precheck: supplier_refund_amount__dbintel_new matches supplier_refund_amount. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE NOT (`supplier_refund_amount` <=> `supplier_refund_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` RENAME COLUMN `supplier_refund_amount` TO `supplier_refund_amount__dbintel_old`;
ALTER TABLE `refunds` RENAME COLUMN `supplier_refund_amount__dbintel_new` TO `supplier_refund_amount`;
