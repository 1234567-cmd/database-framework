-- Step M1226: Rename column service_flights.city_from to city_code_id
-- Direction: down
-- Findings: SCH-058-5a065ebf
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_flights.city_from exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_flights' AND table_schema = DATABASE() AND column_name = 'city_from'
-- Precheck: Column service_flights.city_code_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_flights' AND table_schema = DATABASE() AND column_name = 'city_code_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_flights` RENAME COLUMN `city_code_id` TO `city_from`, ALGORITHM=INPLACE, LOCK=NONE;
