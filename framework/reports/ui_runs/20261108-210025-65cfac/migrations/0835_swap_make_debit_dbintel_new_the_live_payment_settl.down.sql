-- Step M835: Swap: make debit__dbintel_new the live payment_settlement_expenses.debit
-- Direction: down
-- Findings: SCH-023-62c96e33
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of debit__dbintel_new is complete; debit__dbintel_new matches debit
-- Precheck: Backfill of debit__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `payment_settlement_expenses` WHERE `debit__dbintel_new` IS NULL AND `debit` IS NOT NULL
-- Precheck: debit__dbintel_new matches debit. Expect 0: SELECT COUNT(*) FROM `payment_settlement_expenses` WHERE NOT (`debit` <=> `debit__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `payment_settlement_expenses` RENAME COLUMN `debit` TO `debit__dbintel_new`;
ALTER TABLE `payment_settlement_expenses` RENAME COLUMN `debit__dbintel_old` TO `debit`;
