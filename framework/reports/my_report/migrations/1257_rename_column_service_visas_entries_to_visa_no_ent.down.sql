-- Step M1257: Rename column service_visas.entries to visa_no_entry_id
-- Direction: down
-- Findings: SCH-058-7202cd54
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_visas.entries exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_visas' AND table_schema = DATABASE() AND column_name = 'entries'
-- Precheck: Column service_visas.visa_no_entry_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_visas' AND table_schema = DATABASE() AND column_name = 'visa_no_entry_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_visas` RENAME COLUMN `visa_no_entry_id` TO `entries`, ALGORITHM=INPLACE, LOCK=NONE;
