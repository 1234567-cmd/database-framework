-- Step M756: Expand: add tax_amount__dbintel_new decimal(12,4) on invoice_taxes and backfill
-- Direction: up
-- Findings: SCH-023-b8396dd1
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table invoice_taxes exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoice_taxes' AND table_schema = DATABASE()
-- Precheck: Column invoice_taxes.tax_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoice_taxes' AND table_schema = DATABASE() AND column_name = 'tax_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoice_taxes` ADD COLUMN `tax_amount__dbintel_new` decimal(12,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `invoice_taxes` SET `tax_amount__dbintel_new` = `tax_amount` WHERE `tax_amount__dbintel_new` IS NULL AND `tax_amount` IS NOT NULL LIMIT 1000;
