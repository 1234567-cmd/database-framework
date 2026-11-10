-- Step M406: Add column room_types.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-f5cda9e7
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table room_types exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'room_types' AND table_schema = DATABASE()
-- Precheck: Column room_types.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'room_types' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `room_types` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
