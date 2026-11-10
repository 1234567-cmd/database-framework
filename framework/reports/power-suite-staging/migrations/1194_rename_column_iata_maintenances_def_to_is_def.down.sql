-- Step M1194: Rename column iata_maintenances.def to is_def
-- Direction: down
-- Findings: SCH-060-b8c41c91
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column iata_maintenances.def exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iata_maintenances' AND table_schema = DATABASE() AND column_name = 'def'
-- Precheck: Column iata_maintenances.is_def does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'iata_maintenances' AND table_schema = DATABASE() AND column_name = 'is_def'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `iata_maintenances` RENAME COLUMN `is_def` TO `def`, ALGORITHM=INPLACE, LOCK=NONE;
