-- Step M646: Swap: make sst_amount__dbintel_new the live credit_notes.sst_amount
-- Direction: up
-- Findings: SCH-023-017c0744
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of sst_amount__dbintel_new is complete; sst_amount__dbintel_new matches sst_amount
-- Precheck: Backfill of sst_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `sst_amount__dbintel_new` IS NULL AND `sst_amount` IS NOT NULL
-- Precheck: sst_amount__dbintel_new matches sst_amount. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`sst_amount` <=> `sst_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `sst_amount` TO `sst_amount__dbintel_old`;
ALTER TABLE `credit_notes` RENAME COLUMN `sst_amount__dbintel_new` TO `sst_amount`;
