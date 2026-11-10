-- Step M1301: Rename column visa_code_maintenance.length_of_stay to visa_length_stay_id
-- Direction: up
-- Findings: SCH-058-ab354c7d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column visa_code_maintenance.length_of_stay exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_code_maintenance' AND table_schema = DATABASE() AND column_name = 'length_of_stay'
-- Precheck: Column visa_code_maintenance.visa_length_stay_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'visa_code_maintenance' AND table_schema = DATABASE() AND column_name = 'visa_length_stay_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `visa_code_maintenance` RENAME COLUMN `length_of_stay` TO `visa_length_stay_id`, ALGORITHM=INPLACE, LOCK=NONE;
