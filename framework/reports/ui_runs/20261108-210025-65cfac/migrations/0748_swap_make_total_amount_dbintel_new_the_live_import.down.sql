-- Step M748: Swap: make total_amount__dbintel_new the live import_batches.total_amount
-- Direction: down
-- Findings: SCH-023-884420cd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of total_amount__dbintel_new is complete; total_amount__dbintel_new matches total_amount
-- Precheck: Backfill of total_amount__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `import_batches` WHERE `total_amount__dbintel_new` IS NULL AND `total_amount` IS NOT NULL
-- Precheck: total_amount__dbintel_new matches total_amount. Expect 0: SELECT COUNT(*) FROM `import_batches` WHERE NOT (`total_amount` <=> `total_amount__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `import_batches` RENAME COLUMN `total_amount` TO `total_amount__dbintel_new`;
ALTER TABLE `import_batches` RENAME COLUMN `total_amount__dbintel_old` TO `total_amount`;
