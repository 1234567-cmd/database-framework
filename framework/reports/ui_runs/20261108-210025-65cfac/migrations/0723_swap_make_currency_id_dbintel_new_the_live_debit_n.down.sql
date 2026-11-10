-- Step M723: Swap: make currency_id__dbintel_new the live debit_notes.currency_id
-- Direction: down
-- Findings: SCH-039-3ba2087e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of currency_id__dbintel_new is complete; currency_id__dbintel_new matches currency_id
-- Precheck: Backfill of currency_id__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `debit_notes` WHERE `currency_id__dbintel_new` IS NULL AND `currency_id` IS NOT NULL
-- Precheck: currency_id__dbintel_new matches currency_id. Expect 0: SELECT COUNT(*) FROM `debit_notes` WHERE NOT (`currency_id` <=> `currency_id__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `debit_notes` RENAME COLUMN `currency_id` TO `currency_id__dbintel_new`;
ALTER TABLE `debit_notes` RENAME COLUMN `currency_id__dbintel_old` TO `currency_id`;
