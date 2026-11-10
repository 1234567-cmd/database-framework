-- Step M637: Swap: make billing_amount_base__dbintel_new the live credit_notes.billing_amount_base
-- Direction: up
-- Findings: SCH-023-3c63b57f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of billing_amount_base__dbintel_new is complete; billing_amount_base__dbintel_new matches billing_amount_base
-- Precheck: Backfill of billing_amount_base__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `billing_amount_base__dbintel_new` IS NULL AND `billing_amount_base` IS NOT NULL
-- Precheck: billing_amount_base__dbintel_new matches billing_amount_base. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`billing_amount_base` <=> `billing_amount_base__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `billing_amount_base` TO `billing_amount_base__dbintel_old`;
ALTER TABLE `credit_notes` RENAME COLUMN `billing_amount_base__dbintel_new` TO `billing_amount_base`;
