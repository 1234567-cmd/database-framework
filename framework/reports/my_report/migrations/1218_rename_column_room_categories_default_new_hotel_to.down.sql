-- Step M1218: Rename column room_categories.default_new_hotel to is_default_new_hotel
-- Direction: down
-- Findings: SCH-060-8c394401
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column room_categories.default_new_hotel exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'room_categories' AND table_schema = DATABASE() AND column_name = 'default_new_hotel'
-- Precheck: Column room_categories.is_default_new_hotel does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'room_categories' AND table_schema = DATABASE() AND column_name = 'is_default_new_hotel'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `room_categories` RENAME COLUMN `is_default_new_hotel` TO `default_new_hotel`, ALGORITHM=INPLACE, LOCK=NONE;
