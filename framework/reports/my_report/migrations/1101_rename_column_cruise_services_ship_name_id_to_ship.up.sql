-- Step M1101: Rename column cruise_services.ship_name_id to ship_name_maintenance_id
-- Direction: up
-- Findings: SCH-058-67a642ac
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column cruise_services.ship_name_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'ship_name_id'
-- Precheck: Column cruise_services.ship_name_maintenance_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'ship_name_maintenance_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cruise_services` RENAME COLUMN `ship_name_id` TO `ship_name_maintenance_id`, ALGORITHM=INPLACE, LOCK=NONE;
