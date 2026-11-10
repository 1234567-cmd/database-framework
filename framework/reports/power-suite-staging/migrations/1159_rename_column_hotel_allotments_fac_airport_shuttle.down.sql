-- Step M1159: Rename column hotel_allotments.fac_airport_shuttle to is_fac_airport_shuttle
-- Direction: down
-- Findings: SCH-060-d5d062c6
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column hotel_allotments.fac_airport_shuttle exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'fac_airport_shuttle'
-- Precheck: Column hotel_allotments.is_fac_airport_shuttle does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'is_fac_airport_shuttle'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotments` RENAME COLUMN `is_fac_airport_shuttle` TO `fac_airport_shuttle`, ALGORITHM=INPLACE, LOCK=NONE;
