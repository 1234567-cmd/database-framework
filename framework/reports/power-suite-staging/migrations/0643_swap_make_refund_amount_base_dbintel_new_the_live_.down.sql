-- Step M643: Swap: make refund_amount_base__dbintel_new the live credit_notes.refund_amount_base
-- Direction: down
-- Findings: SCH-023-40015cc7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Requires data repair if the prechecks fail: Backfill of refund_amount_base__dbintel_new is complete; refund_amount_base__dbintel_new matches refund_amount_base
-- Precheck: Backfill of refund_amount_base__dbintel_new is complete. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE `refund_amount_base__dbintel_new` IS NULL AND `refund_amount_base` IS NOT NULL
-- Precheck: refund_amount_base__dbintel_new matches refund_amount_base. Expect 0: SELECT COUNT(*) FROM `credit_notes` WHERE NOT (`refund_amount_base` <=> `refund_amount_base__dbintel_new`)
-- Note: The application should tolerate both types before this step and deploy between expand and swap (MIG-004).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `credit_notes` RENAME COLUMN `refund_amount_base` TO `refund_amount_base__dbintel_new`;
ALTER TABLE `credit_notes` RENAME COLUMN `refund_amount_base__dbintel_old` TO `refund_amount_base`;
