-- Step M628: Swap: make base_amount__dbintel_new the live credit_notes.base_amount
-- Direction: up
-- Findings: SCH-023-5c2272ba
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of base_amount__dbintel_new is complete; base_amount__dbintel_new matches base_amount
-- Precheck: Backfill of base_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `base_amount__dbintel_new` IS NULL AND `base_amount` IS NOT NULL
-- Precheck: base_amount__dbintel_new matches base_amount. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`base_amount` <=> `base_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `base_amount` TO `base_amount__dbintel_old`;
ALTER TABLE `credit_notes` RENAME COLUMN `base_amount__dbintel_new` TO `base_amount`;
