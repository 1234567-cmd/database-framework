-- Step M892: Swap: make supplier_refund_amount_base__dbintel_new the live refunds.supplier_refund_amount_base
-- Direction: down
-- Findings: SCH-023-438ab36f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of supplier_refund_amount_base__dbintel_new is complete; supplier_refund_amount_base__dbintel_new matches supplier_refund_amount_base
-- Precheck: Backfill of supplier_refund_amount_base__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE `supplier_refund_amount_base__dbintel_new` IS NULL AND `supplier_refund_amount_base` IS NOT NULL
-- Precheck: supplier_refund_amount_base__dbintel_new matches supplier_refund_amount_base. Expect 0: SELECT COUNT(*) FROM `refunds` WHERE NOT (`supplier_refund_amount_base` <=> `supplier_refund_amount_base__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `refunds` RENAME COLUMN `supplier_refund_amount_base` TO `supplier_refund_amount_base__dbintel_new`;
ALTER TABLE `refunds` RENAME COLUMN `supplier_refund_amount_base__dbintel_old` TO `supplier_refund_amount_base`;
