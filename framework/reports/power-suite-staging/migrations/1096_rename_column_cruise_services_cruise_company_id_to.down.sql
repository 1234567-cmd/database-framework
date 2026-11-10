-- Step M1096: Rename column cruise_services.cruise_company_id to cruise_company_maintenance_id
-- Direction: down
-- Findings: SCH-058-8337dd95
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column cruise_services.cruise_company_id exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'cruise_company_id'
-- Precheck: Column cruise_services.cruise_company_maintenance_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cruise_services' AND table_schema = DATABASE() AND column_name = 'cruise_company_maintenance_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cruise_services` RENAME COLUMN `cruise_company_maintenance_id` TO `cruise_company_id`, ALGORITHM=INPLACE, LOCK=NONE;
