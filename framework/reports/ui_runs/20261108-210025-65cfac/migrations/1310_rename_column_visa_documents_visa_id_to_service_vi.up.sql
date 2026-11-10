-- Step M1310: Rename column visa_documents.visa_id to service_visa_id
-- Direction: up
-- Findings: SCH-058-d556987f
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column visa_documents.visa_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_documents' AND table_schema = DATABASE() AND column_name = 'visa_id'
-- Precheck: Column visa_documents.service_visa_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_documents' AND table_schema = DATABASE() AND column_name = 'service_visa_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_documents` RENAME COLUMN `visa_id` TO `service_visa_id`, ALGORITHM=INPLACE, LOCK=NONE;
