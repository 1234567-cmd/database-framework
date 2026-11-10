-- Step M1258: Rename column service_visas.length_of_stay to visa_length_stay_id
-- Direction: down
-- Findings: SCH-058-4ea02988
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_visas.length_of_stay exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_visas' AND table_schema = DATABASE() AND column_name = 'length_of_stay'
-- Precheck: Column service_visas.visa_length_stay_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_visas' AND table_schema = DATABASE() AND column_name = 'visa_length_stay_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_visas` RENAME COLUMN `visa_length_stay_id` TO `length_of_stay`, ALGORITHM=INPLACE, LOCK=NONE;
