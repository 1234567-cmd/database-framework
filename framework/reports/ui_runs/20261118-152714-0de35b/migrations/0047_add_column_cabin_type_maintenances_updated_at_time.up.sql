-- Step M047: Add column cabin_type_maintenances.updated_at timestamp
-- Direction: up
-- Findings: DE-005-07d462d5, SCH-044-9bf074c0
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table cabin_type_maintenances exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'cabin_type_maintenances' AND table_schema = DATABASE()
-- Precheck: Column cabin_type_maintenances.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'cabin_type_maintenances' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `cabin_type_maintenances` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
