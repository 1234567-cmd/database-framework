-- Step M250: Add column issued_document_numbers.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-d9d45899
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table issued_document_numbers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'issued_document_numbers' AND table_schema = DATABASE()
-- Precheck: Column issued_document_numbers.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'issued_document_numbers' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `issued_document_numbers` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
