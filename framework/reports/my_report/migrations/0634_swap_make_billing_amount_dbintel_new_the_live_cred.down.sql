-- Step M634: Swap: make billing_amount__dbintel_new the live credit_notes.billing_amount
-- Direction: down
-- Findings: SCH-023-d43cede2
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of billing_amount__dbintel_new is complete; billing_amount__dbintel_new matches billing_amount
-- Precheck: Backfill of billing_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `billing_amount__dbintel_new` IS NULL AND `billing_amount` IS NOT NULL
-- Precheck: billing_amount__dbintel_new matches billing_amount. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`billing_amount` <=> `billing_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `billing_amount` TO `billing_amount__dbintel_new`;
ALTER TABLE `credit_notes` RENAME COLUMN `billing_amount__dbintel_old` TO `billing_amount`;
