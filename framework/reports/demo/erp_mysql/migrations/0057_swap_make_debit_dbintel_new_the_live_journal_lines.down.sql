-- Step M057: Swap: make debit__dbintel_new the live journal_lines.debit
-- Direction: down
-- Findings: SCH-020-fa680358
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of debit__dbintel_new is complete; debit__dbintel_new matches debit
-- Precheck: Backfill of debit__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `journal_lines` WHERE `debit__dbintel_new` IS NULL AND `debit` IS NOT NULL
-- Precheck: debit__dbintel_new matches debit. Expect 0: SELECT COUNT(*) FROM `journal_lines` WHERE NOT (`debit` <=> `debit__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `journal_lines` RENAME COLUMN `debit` TO `debit__dbintel_new`;
ALTER TABLE `journal_lines` RENAME COLUMN `debit__dbintel_old` TO `debit`;
