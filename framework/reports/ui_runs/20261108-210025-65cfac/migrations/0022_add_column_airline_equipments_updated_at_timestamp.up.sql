-- Step M022: Add column airline_equipments.updated_at timestamp
-- Direction: up
-- Findings: DE-005-e0deae3c, SCH-044-8c55ee06
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table airline_equipments exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'airline_equipments' AND table_schema = DATABASE()
-- Precheck: Column airline_equipments.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'airline_equipments' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `airline_equipments` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
