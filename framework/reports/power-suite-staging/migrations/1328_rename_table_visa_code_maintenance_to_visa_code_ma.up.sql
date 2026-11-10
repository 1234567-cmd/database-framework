-- Step M1328: Rename table visa_code_maintenance to visa_code_maintenances
-- Direction: up
-- Findings: SCH-055-d93c3330
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table visa_code_maintenance exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'visa_code_maintenance' AND table_schema = DATABASE()
-- Note: Renaming a table breaks every reader that uses the old name. Consider a compatibility view for one release.
-- Dependency risk: Foreign key from service_visas references visa_code_maintenance.
-- Dependency risk: Foreign key from visa_code_require_codes references visa_code_maintenance.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
RENAME TABLE `visa_code_maintenance` TO `visa_code_maintenances`;
