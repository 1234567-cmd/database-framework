-- Step M714: Swap: make amount_base__dbintel_new the live debit_notes.amount_base
-- Direction: down
-- Findings: SCH-023-0e0e1e71
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of amount_base__dbintel_new is complete; amount_base__dbintel_new matches amount_base
-- Precheck: Backfill of amount_base__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `debit_notes` WHERE `amount_base__dbintel_new` IS NULL AND `amount_base` IS NOT NULL
-- Precheck: amount_base__dbintel_new matches amount_base. Expect 0: SELECT COUNT(*) FROM `debit_notes` WHERE NOT (`amount_base` <=> `amount_base__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` RENAME COLUMN `amount_base` TO `amount_base__dbintel_new`;
ALTER TABLE `debit_notes` RENAME COLUMN `amount_base__dbintel_old` TO `amount_base`;
