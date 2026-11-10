-- Step M771: Expand: add invoice_amount__dbintel_new decimal(17,4) on iur_upload_logs and backfill
-- Direction: up
-- Findings: SCH-023-d91a2f47
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: medium.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table iur_upload_logs exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'iur_upload_logs' AND table_schema = DATABASE()
-- Precheck: Column iur_upload_logs.invoice_amount exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iur_upload_logs' AND table_schema = DATABASE() AND column_name = 'invoice_amount'
-- Note: The backfill is one batch; run it repeatedly, throttled, outside any DDL transaction until it updates no rows (MIG-012).
-- Note: The application must write both columns, or a sync trigger must exist, from this step until the swap; otherwise later writes are missed and the swap precheck fails (MIG-004, MIG-016).
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iur_upload_logs` ADD COLUMN `invoice_amount__dbintel_new` decimal(17,4), ALGORITHM=INPLACE, LOCK=NONE;
UPDATE `iur_upload_logs` SET `invoice_amount__dbintel_new` = `invoice_amount` WHERE `invoice_amount__dbintel_new` IS NULL AND `invoice_amount` IS NOT NULL LIMIT 1000;
