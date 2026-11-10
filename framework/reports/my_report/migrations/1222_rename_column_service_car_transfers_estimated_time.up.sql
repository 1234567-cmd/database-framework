-- Step M1222: Rename column service_car_transfers.estimated_time_departure to estimated_time_departure_at
-- Direction: up
-- Findings: SCH-061-836a6563
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_car_transfers.estimated_time_departure exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_car_transfers' AND table_schema = DATABASE() AND column_name = 'estimated_time_departure'
-- Precheck: Column service_car_transfers.estimated_time_departure_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_car_transfers' AND table_schema = DATABASE() AND column_name = 'estimated_time_departure_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_car_transfers` RENAME COLUMN `estimated_time_departure` TO `estimated_time_departure_at`, ALGORITHM=INPLACE, LOCK=NONE;
