-- Step M772: Swap: make invoice_amount__dbintel_new the live iur_upload_logs.invoice_amount
-- Direction: down
-- Findings: SCH-023-d91a2f47
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of invoice_amount__dbintel_new is complete; invoice_amount__dbintel_new matches invoice_amount
-- Precheck: Backfill of invoice_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `iur_upload_logs` WHERE `invoice_amount__dbintel_new` IS NULL AND `invoice_amount` IS NOT NULL
-- Precheck: invoice_amount__dbintel_new matches invoice_amount. Expect 0: SELECT COUNT(*) FROM `iur_upload_logs` WHERE NOT (`invoice_amount` <=> `invoice_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_upload_logs` RENAME COLUMN `invoice_amount` TO `invoice_amount__dbintel_new`;
ALTER TABLE `iur_upload_logs` RENAME COLUMN `invoice_amount__dbintel_old` TO `invoice_amount`;
