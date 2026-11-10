-- Step M1246: Rename column service_rental_cars.drop_off_date_time to drop_off_date_at
-- Direction: up
-- Findings: SCH-061-3b51ac6c
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_rental_cars.drop_off_date_time exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_rental_cars' AND table_schema = DATABASE() AND column_name = 'drop_off_date_time'
-- Precheck: Column service_rental_cars.drop_off_date_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_rental_cars' AND table_schema = DATABASE() AND column_name = 'drop_off_date_at'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_rental_cars` RENAME COLUMN `drop_off_date_time` TO `drop_off_date_at`, ALGORITHM=INPLACE, LOCK=NONE;
