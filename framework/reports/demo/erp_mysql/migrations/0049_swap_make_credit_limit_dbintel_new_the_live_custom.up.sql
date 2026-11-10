-- Step M049: Swap: make credit_limit__dbintel_new the live customers.credit_limit
-- Direction: up
-- Findings: SCH-020-639966f4
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of credit_limit__dbintel_new is complete; credit_limit__dbintel_new matches credit_limit
-- Precheck: Backfill of credit_limit__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `customers` WHERE `credit_limit__dbintel_new` IS NULL AND `credit_limit` IS NOT NULL
-- Precheck: credit_limit__dbintel_new matches credit_limit. Expect 0: SELECT COUNT(*) FROM `customers` WHERE NOT (`credit_limit` <=> `credit_limit__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customers` RENAME COLUMN `credit_limit` TO `credit_limit__dbintel_old`;
ALTER TABLE `customers` RENAME COLUMN `credit_limit__dbintel_new` TO `credit_limit`;
