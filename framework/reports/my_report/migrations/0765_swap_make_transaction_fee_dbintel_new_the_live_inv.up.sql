-- Step M765: Swap: make transaction_fee__dbintel_new the live invoices.transaction_fee
-- Direction: up
-- Findings: SCH-020-522068ff
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of transaction_fee__dbintel_new is complete; transaction_fee__dbintel_new matches transaction_fee
-- Precheck: Backfill of transaction_fee__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `invoices` WHERE `transaction_fee__dbintel_new` IS NULL AND `transaction_fee` IS NOT NULL
-- Precheck: transaction_fee__dbintel_new matches transaction_fee. Expect 0: SELECT COUNT(*) FROM `invoices` WHERE NOT (`transaction_fee` <=> `transaction_fee__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoices` RENAME COLUMN `transaction_fee` TO `transaction_fee__dbintel_old`;
ALTER TABLE `invoices` RENAME COLUMN `transaction_fee__dbintel_new` TO `transaction_fee`;
