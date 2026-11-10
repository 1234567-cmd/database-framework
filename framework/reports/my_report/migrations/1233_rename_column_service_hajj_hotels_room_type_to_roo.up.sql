-- Step M1233: Rename column service_hajj_hotels.room_type to room_type_id
-- Direction: up
-- Findings: SCH-058-1e77ccc7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Column service_hajj_hotels.room_type exists. Expect 1: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_hotels' AND table_schema = DATABASE() AND column_name = 'room_type'
-- Precheck: Column service_hajj_hotels.room_type_id does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_hajj_hotels' AND table_schema = DATABASE() AND column_name = 'room_type_id'
-- Note: Renames break every reader that uses the old name. On live systems add a compatible column and migrate callers first (MIG-004).
-- Note: RENAME COLUMN needs MySQL 8.0 or later; earlier versions need CHANGE with the full column definition.
-- Dependency risk: Application code, ORM mappings, reports and ETL jobs outside the database are not analyzed by the migration generator and may use this name.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_hajj_hotels` RENAME COLUMN `room_type` TO `room_type_id`, ALGORITHM=INPLACE, LOCK=NONE;
