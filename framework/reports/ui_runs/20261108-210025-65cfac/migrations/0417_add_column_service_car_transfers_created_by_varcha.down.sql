-- Step M417: Add column service_car_transfers.created_by varchar(255)
-- Direction: down
-- Findings: SCH-044-70fa2f86
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table service_car_transfers exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'service_car_transfers' AND table_schema = DATABASE()
-- Precheck: Column service_car_transfers.created_by does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'service_car_transfers' AND table_schema = DATABASE() AND column_name = 'created_by'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `service_car_transfers` DROP COLUMN `created_by`, ALGORITHM=INPLACE, LOCK=NONE;
