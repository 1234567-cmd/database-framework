-- Step M241: Add column invoice_settings.created_at timestamp
-- Direction: up
-- Findings: SCH-044-cfc68ca7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table invoice_settings exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'invoice_settings' AND table_schema = DATABASE()
-- Precheck: Column invoice_settings.created_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'invoice_settings' AND table_schema = DATABASE() AND column_name = 'created_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `invoice_settings` ADD COLUMN `created_at` timestamp DEFAULT CURRENT_TIMESTAMP, ALGORITHM=INPLACE, LOCK=NONE;
