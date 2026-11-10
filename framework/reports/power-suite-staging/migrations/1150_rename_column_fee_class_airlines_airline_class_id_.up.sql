-- Step M1150: Rename column fee_class_airlines.airline_class_id to airline_class_code_id
-- Direction: up
-- Findings: SCH-058-735efbcd
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column fee_class_airlines.airline_class_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_class_airlines' AND table_schema = DATABASE() AND column_name = 'airline_class_id'
-- Precheck: Column fee_class_airlines.airline_class_code_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'fee_class_airlines' AND table_schema = DATABASE() AND column_name = 'airline_class_code_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `fee_class_airlines` RENAME COLUMN `airline_class_id` TO `airline_class_code_id`, ALGORITHM=INPLACE, LOCK=NONE;
