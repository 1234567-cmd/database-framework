-- Step M142: Add column customer_required_data_profiles.updated_at timestamp
-- Direction: up
-- Findings: DE-005-6901c6c1, SCH-044-6a6d9a80
-- Destructive: False. Reversible: True. Data loss risk: none. Lock risk: low.
-- PROPOSAL ONLY. Review before use.
-- Precheck: Table customer_required_data_profiles exists. Expect 1: SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE()
-- Precheck: Column customer_required_data_profiles.updated_at does not exist. Expect 0: SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'customer_required_data_profiles' AND table_schema = DATABASE() AND column_name = 'updated_at'
-- Note: Rollback drops the column and discards any values written to it after the change.
-- Note: MySQL 8.0 allows ADD COLUMN with INPLACE and LOCK=NONE; INSTANT may also be available from 8.0.12 and later.
SET SESSION lock_wait_timeout = 5;
ALTER TABLE `customer_required_data_profiles` ADD COLUMN `updated_at` timestamp, ALGORITHM=INPLACE, LOCK=NONE;
