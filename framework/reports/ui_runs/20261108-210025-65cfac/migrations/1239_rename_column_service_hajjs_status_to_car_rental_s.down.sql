-- Step M1239: Rename column service_hajjs.status to car_rental_status_id
-- Direction: down
-- Findings: SCH-058-c02566e3
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_hajjs.status exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajjs' AND table_schema = DATABASE() AND column_name = 'status'
-- Precheck: Column service_hajjs.car_rental_status_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajjs' AND table_schema = DATABASE() AND column_name = 'car_rental_status_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: View refunds_with_conversion references service_hajjs.status; check its definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hajjs` RENAME COLUMN `car_rental_status_id` TO `status`, ALGORITHM=INPLACE, LOCK=NONE;
