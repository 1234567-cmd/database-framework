-- Step M494: Add column special_seat.updated_at timestamp
-- Direction: down
-- Findings: DE-005-179231c7, SCH-044-1f7089e8
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table special_seat exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'special_seat' AND table_schema = DATABASE()
-- Precheck: Column special_seat.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'special_seat' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `special_seat` DROP COLUMN `updated_at`, ALGORITHM=INPLACE, LOCK=NONE;
