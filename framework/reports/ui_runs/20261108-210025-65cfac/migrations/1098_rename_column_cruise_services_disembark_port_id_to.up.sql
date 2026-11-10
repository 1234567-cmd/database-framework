-- Step M1098: Rename column cruise_services.disembark_port_id to seaport_code_maintenance_id
-- Direction: up
-- Findings: SCH-058-101a2dfe
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column cruise_services.disembark_port_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'disembark_port_id'
-- Precheck: Column cruise_services.seaport_code_maintenance_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'seaport_code_maintenance_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cruise_services` RENAME COLUMN `disembark_port_id` TO `seaport_code_maintenance_id`, ALGORITHM=INPLACE, LOCK=NONE;
