-- Step M649: Swap: make used_amount__dbintel_new the live credit_notes.used_amount
-- Direction: up
-- Findings: SCH-023-b702b1da
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of used_amount__dbintel_new is complete; used_amount__dbintel_new matches used_amount
-- Precheck: Backfill of used_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `used_amount__dbintel_new` IS NULL AND `used_amount` IS NOT NULL
-- Precheck: used_amount__dbintel_new matches used_amount. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`used_amount` <=> `used_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `used_amount` TO `used_amount__dbintel_old`;
ALTER TABLE `credit_notes` RENAME COLUMN `used_amount__dbintel_new` TO `used_amount`;
