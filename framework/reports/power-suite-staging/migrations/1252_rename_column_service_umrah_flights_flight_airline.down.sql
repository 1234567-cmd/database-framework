-- Step M1252: Rename column service_umrah_flights.flight_airline_id to airline_code_id
-- Direction: down
-- Findings: SCH-058-4d419f5d
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_umrah_flights.flight_airline_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_umrah_flights' AND table_schema = DATABASE() AND column_name = 'flight_airline_id'
-- Precheck: Column service_umrah_flights.airline_code_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_umrah_flights' AND table_schema = DATABASE() AND column_name = 'airline_code_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_umrah_flights` RENAME COLUMN `airline_code_id` TO `flight_airline_id`, ALGORITHM=INPLACE, LOCK=NONE;
