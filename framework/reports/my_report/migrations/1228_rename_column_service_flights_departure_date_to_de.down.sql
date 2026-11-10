-- Step M1228: Rename column service_flights.departure_date to departure_at
-- Direction: down
-- Findings: SCH-061-4736a2f0
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_flights.departure_date exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_flights' AND table_schema = DATABASE() AND column_name = 'departure_date'
-- Precheck: Column service_flights.departure_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_flights' AND table_schema = DATABASE() AND column_name = 'departure_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_flights` RENAME COLUMN `departure_at` TO `departure_date`, ALGORITHM=INPLACE, LOCK=NONE;
