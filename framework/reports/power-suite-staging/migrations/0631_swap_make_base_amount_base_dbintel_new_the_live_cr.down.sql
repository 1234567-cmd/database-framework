-- Step M631: Swap: make base_amount_base__dbintel_new the live credit_notes.base_amount_base
-- Direction: down
-- Findings: SCH-023-09e64841
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of base_amount_base__dbintel_new is complete; base_amount_base__dbintel_new matches base_amount_base
-- Precheck: Backfill of base_amount_base__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `base_amount_base__dbintel_new` IS NULL AND `base_amount_base` IS NOT NULL
-- Precheck: base_amount_base__dbintel_new matches base_amount_base. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`base_amount_base` <=> `base_amount_base__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `base_amount_base` TO `base_amount_base__dbintel_new`;
ALTER TABLE `credit_notes` RENAME COLUMN `base_amount_base__dbintel_old` TO `base_amount_base`;
