-- Step M1158: Rename column hotel_allotments.fac_24_hour_front_desk to is_fac_24_hour_front_desk
-- Direction: down
-- Findings: SCH-060-4153d7ad
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column hotel_allotments.fac_24_hour_front_desk exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'fac_24_hour_front_desk'
-- Precheck: Column hotel_allotments.is_fac_24_hour_front_desk does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hotel_allotments' AND table_schema = DATABASE() AND column_name = 'is_fac_24_hour_front_desk'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `hotel_allotments` RENAME COLUMN `is_fac_24_hour_front_desk` TO `fac_24_hour_front_desk`, ALGORITHM=INPLACE, LOCK=NONE;
