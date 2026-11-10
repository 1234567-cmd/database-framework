-- Step M1201: Rename column maintenance_fee_groups.validity_period_to to validity_period_to_date
-- Direction: down
-- Findings: SCH-061-2a6c812e
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column maintenance_fee_groups.validity_period_to exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE() AND column_name = 'validity_period_to'
-- Precheck: Column maintenance_fee_groups.validity_period_to_date does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'maintenance_fee_groups' AND table_schema = DATABASE() AND column_name = 'validity_period_to_date'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `maintenance_fee_groups` RENAME COLUMN `validity_period_to_date` TO `validity_period_to`, ALGORITHM=INPLACE, LOCK=NONE;
