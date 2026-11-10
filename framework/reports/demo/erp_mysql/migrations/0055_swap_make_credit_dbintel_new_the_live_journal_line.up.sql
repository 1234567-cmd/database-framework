-- Step M055: Swap: make credit__dbintel_new the live journal_lines.credit
-- Direction: up
-- Findings: SCH-020-129ee72d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of credit__dbintel_new is complete; credit__dbintel_new matches credit
-- Precheck: Backfill of credit__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `journal_lines` WHERE `credit__dbintel_new` IS NULL AND `credit` IS NOT NULL
-- Precheck: credit__dbintel_new matches credit. Expect 0: SELECT COUNT(*) FROM `journal_lines` WHERE NOT (`credit` <=> `credit__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_lines` RENAME COLUMN `credit` TO `credit__dbintel_old`;
ALTER TABLE `journal_lines` RENAME COLUMN `credit__dbintel_new` TO `credit`;
